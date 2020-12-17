import os
import time
from collections import defaultdict
import supervisely_lib as sly

# ignore_task_id=True allows to access data in different workspaces with the same API object.
# It is disabled by default to protect data from other workspaces
my_app = sly.AppService(ignore_task_id=True)

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID1 = int(os.environ['modal.state.projectId1'])
PROJECT1 = None
META1: sly.ProjectMeta = None
PROJECT_ID2 = int(os.environ['modal.state.projectId2'])
PROJECT2 = None
META2: sly.ProjectMeta = None
RESULTS = None
RESULTS_DATA = None


def process_items(ds_info1, collection1, ds_info2, collection2):
    global RESULTS, RESULTS_DATA
    ds_names = ds_info1.keys() | ds_info2.keys()

    results = []
    results_data = []
    for idx, name in enumerate(ds_names):
        compare = {"dsIndex": idx}
        images1 = collection1.get(name, [])
        images2 = collection2.get(name, [])
        if len(images1) == 0:
            compare["message"] = ["new dataset (right)"]
            #compare["icon"] = [["zmdi zmdi-long-arrow-left", "zmdi zmdi-alert-circle-o"]]
            compare["icon"] = [["zmdi zmdi-folder-outline"]]
            compare["color"] = ["#F39C12"]
            compare["numbers"] = [-1]
            compare["left"] = {"name": ""}
            compare["right"] = {"name": name, "count": len(images2)}
            results_data.append([images2])
        elif len(images2) == 0:
            compare["message"] = ["new dataset (left)"]
            #compare["infoIcon"] = [["zmdi zmdi-alert-circle-o", "zmdi zmdi-long-arrow-right"]]
            compare["icon"] = [["zmdi zmdi-folder-outline"]]
            compare["color"] = ["#F39C12"]
            compare["numbers"] = [-1]
            compare["left"] = {"name": name, "count": len(images1)}
            compare["right"] = {"name": ""}
            results_data.append([images1])
        else:
            img_dict1 = {img_info.name: img_info for img_info in images1}
            img_dict2 = {img_info.name: img_info for img_info in images2}

            matched = []
            diff = []  # same names but different hashes or image sizes
            same_names = img_dict1.keys() & img_dict2.keys()
            for img_name in same_names:
                dest = matched if img_dict1[img_name].hash == img_dict2[img_name].hash else diff
                dest.extend([img_dict1[img_name], img_dict2[img_name]])

            uniq1 = [img_dict1[name] for name in img_dict1.keys() - same_names]
            uniq2 = [img_dict2[name] for name in img_dict2.keys() - same_names]

            compare["message"] = ["matched", "conflicts", "unique (left)", "unique (right)"]
            compare["icon"] = [["zmdi zmdi-check"], ["zmdi zmdi-close"], ["zmdi zmdi-plus-circle-o"], ["zmdi zmdi-plus-circle-o"]]
            compare["color"] = ["green", "red", "#20a0ff", "#20a0ff"]
            compare["numbers"] = [len(matched) / 2, len(diff) / 2, len(uniq1), len(uniq2)]
            compare["left"] = {"name": name, "count": len(images1)}
            compare["right"] = {"name": name, "count": len(images2)}
            results_data.append([matched, diff, uniq1, uniq2])

        results.append(compare)

    RESULTS = results
    RESULTS_DATA = results_data
    return results


def _get_all_images(api: sly.Api, project):
    ds_info = {}
    ds_images = {}
    ws_to_team = {}
    for dataset in api.dataset.get_list(project.id):
        ds_info[dataset.name] = dataset
        images = api.image.get_list(dataset.id)
        modified_images = []
        for image_info in images:
            if project.workspace_id not in ws_to_team:
                ws_to_team[project.workspace_id] = api.workspace.get_info_by_id(project.workspace_id).team_id
            meta = {
                "team_id": ws_to_team[project.workspace_id],
                "workspace_id": project.workspace_id,
                "project_id": project.id,
                "project_name": project.name,
                "dataset_name": dataset.name
            }
            image_info = image_info._replace(meta=meta)
            modified_images.append(image_info)
        ds_images[dataset.name] = modified_images
    return ds_info, ds_images


@my_app.callback("show_images")
@sly.timeit
def show_images(api: sly.Api, task_id, context, state, app_logger):
    click = state.get("click", None)
    if click is None:
        return
    clickIndex = state["clickIndex"]
    images = RESULTS_DATA[click["dsIndex"]][clickIndex]
    data = []
    for idx, info in enumerate(images):
        data.append([
            idx + 1,
            info.meta["project_id"],
            info.meta["project_name"],
            info.dataset_id,
            info.meta["dataset_name"],
            info.id,
            '<a href="{0}" rel="noopener noreferrer" target="_blank">{1}</a>'
            .format(api.image.url(info.meta["team_id"],
                                  info.meta["workspace_id"],
                                  info.meta["project_id"],
                                  info.dataset_id,
                                  info.id),
                    info.name),
        ])
    cell_table = {
        "columns": ["#", "project id", "project", "dataset id", "dataset", "image id", "image"],
        "data": data
    }
    fields = [
        {"field": "data.images", "payload": cell_table},
    ]
    api.app.set_fields(task_id, fields)


def init_ui(api: sly.Api, task_id, app_logger):
    global PROJECT1, PROJECT2, META1, META2, CLASSES_INFO, TAGS_INFO

    PROJECT1 = api.project.get_info_by_id(PROJECT_ID1)
    PROJECT2 = api.project.get_info_by_id(PROJECT_ID2)

    if PROJECT1.type != PROJECT2.type:
        raise TypeError(f"Projects have different types: {str(PROJECT1.type)} != {str(PROJECT2.type)}")

    META1 = sly.ProjectMeta.from_json(api.project.get_meta(PROJECT_ID1))
    META2 = sly.ProjectMeta.from_json(api.project.get_meta(PROJECT_ID2))

    ds_info1, ds_images1 = _get_all_images(api, PROJECT1)
    ds_info2, ds_images2 = _get_all_images(api, PROJECT2)

    result = process_items(ds_info1, ds_images1, ds_info2, ds_images2)

    data = {
        "projectId1": PROJECT1.id,
        "projectName1": PROJECT1.name,
        "projectPreviewUrl1": api.image.preview_url(PROJECT1.reference_image_url, 100, 100),
        "projectId2": PROJECT2.id,
        "projectName2": PROJECT2.name,
        "projectPreviewUrl2": api.image.preview_url(PROJECT2.reference_image_url, 100, 100),
        "table": result,
        "images": {"columns": [], "data": []},
        "mergeOptions": ["unify", "intersect"],
        "resolveOptions": ["skip image", "use left", "use right"],
        "createdProjectId": None,
        "createdProjectName": None,
        "mergeTagsOptions": ["combine", "use left", "use right"],
        "mergeLabelsOptions": ["combine", "use left", "use right"],
        "mergeMetadataOptions": ["combine", "use left", "use right"],
        "progressCurrent": 0,
        "progressTotal": 0,
        "progress": 0,
        "started": False,
    }
    state = {
        "merge": "unify",
        "mergeTags": "combine",
        "mergeLabels": "combine",
        "mergeMetadata": "combine",
        "resolve": "skip image",
        "teamId": TEAM_ID,
        "workspaceId": WORKSPACE_ID,
        "resultProjectId": None,
        "click": None,
        "clickIndex": None
    }
    return data, state

def _increment_progress(api, task_id, progress):
    progress.iter_done_report()
    fields = [
        {"field": "data.progressCurrent", "payload": progress.current},
        {"field": "data.progress", "payload": int(100 * progress.current / progress.total)},
    ]
    api.app.set_fields(task_id, fields)

@my_app.callback("merge")
@sly.timeit
def merge(api: sly.Api, task_id, context, state, app_logger):
    progress_total = sum([len(c["message"]) for c in RESULTS])
    fields = [
        {"field": "data.started", "payload": True},
        {"field": "data.progressTotal", "payload": progress_total},
    ]
    api.app.set_fields(task_id, fields)

    # result project has to be empty
    result_project_id = state["resultProjectId"]
    if result_project_id is None:
        my_app.logger.warn("Result project id is not defined")
        return
    result_project = api.project.get_info_by_id(result_project_id)
    if result_project is None:
        my_app.logger.warn("Result project not found")
        return
    res_datasets = api.dataset.get_list(result_project.id)
    if len(res_datasets) != 0:
        my_app.logger.warn("Result project is not empty, choose another one")
        return
    res_meta = sly.ProjectMeta.from_json(api.project.get_meta(result_project.id))

    def _add_simple(res_dataset, images, ds_name):
        image_ids = []
        image_names = []
        image_metas = []
        for info in images:
            image_ids.append(info.id)
            image_names.append(info.name)
            image_metas.append(info.meta)

        if res_dataset is None:
            res_dataset = api.dataset.create(result_project.id, ds_name)
        uploaded_images = api.image.upload_ids(res_dataset.id, image_names, image_ids, metas=image_metas)
        uploaded_ids = [info.id for info in uploaded_images]

        anns_json = [ann_info.annotation for ann_info in api.annotation.download_batch(images[0].dataset_id, image_ids)]
        api.annotation.upload_jsons(uploaded_ids, anns_json)
        return res_dataset

    progress = sly.Progress("Processing", progress_total)

    for compare, items in zip(RESULTS, RESULTS_DATA):
        #@TODO: for debug
        time.sleep(5)
        for idx, message in enumerate(compare["message"]):
            images = items[idx]
            if len(images) == 0:
                _increment_progress(api, task_id, progress)
                continue

            left_ds = compare["left"]["name"]
            right_ds = compare["right"]["name"]

            app_logger.info("[{}] LEFT: {!r} RIGHT: {!r}".format(len(images), left_ds, right_ds))

            if left_ds != "":
                res_dataset = api.dataset.get_info_by_name(result_project.id, left_ds)
            if right_ds != "" and res_dataset is not None:
                res_dataset = api.dataset.get_info_by_name(result_project.id, right_ds)

            # "matched", "conflicts", "unique (left)", "unique (right)"
            if message == "matched":
                left_ds_id = api.dataset.get_info_by_name(PROJECT1.id, left_ds).id
                right_ds_id = api.dataset.get_info_by_name(PROJECT2.id, right_ds).id

                image_ids, image_names = defaultdict(list), defaultdict(list)
                matched_pairs = defaultdict(lambda: defaultdict(int))
                for image_info in images:
                    if res_dataset is None:
                        res_dataset = api.dataset.create(result_project.id, left_ds)
                    image_ids[image_info.dataset_id].append(image_info.id)
                    image_names[image_info.dataset_id].append(image_info.name)
                    if image_info.dataset_id == left_ds_id:
                        matched_pairs[image_info.name][left_ds_id] = image_info
                    elif image_info.dataset_id == right_ds_id:
                        matched_pairs[image_info.name][right_ds_id] = image_info

                #merge metadata for matched pairs
                metas = {}
                for image_name in matched_pairs.keys():
                    left_info = matched_pairs[image_name][left_ds_id]
                    right_info = matched_pairs[image_name][right_ds_id]
                    res_image_meta = {}
                    if state["mergeMetadata"] == "combine":
                        res_image_meta["left"] = {"image_id": left_info.id, "data": left_info.meta}
                        res_image_meta["right"] = {"image_id": right_info.id, "data": right_info.meta}
                    elif state["mergeMetadata"] == "use left":
                        res_image_meta = left_info.meta
                    elif state["mergeMetadata"] == "use right":
                        res_image_meta = right_info.meta
                    metas[image_name] = res_image_meta

                #uplaod images for matched pairs
                uploaded_images = None
                for dataset_id in image_ids.keys():
                    uploaded_images = api.image.upload_ids(res_dataset.id, image_names[dataset_id], image_ids[dataset_id],
                                                           metas=[metas[image_name] for image_name in image_names[dataset_id]])
                    break
                uploaded_ids = {info.name: info.id for info in uploaded_images}

                left_image_ids = []
                right_image_ids = []
                res_image_ids = []
                for image_name in matched_pairs.keys():
                    left_info = matched_pairs[image_name][left_ds_id]
                    left_image_ids.append(left_info.id)

                    right_info = matched_pairs[image_name][right_ds_id]
                    right_image_ids.append(right_info.id)

                    res_image_ids.append(uploaded_ids[image_name])

                left_anns = api.annotation.download_batch(left_ds_id, left_image_ids)
                right_anns = api.annotation.download_batch(right_ds_id, right_image_ids)
                anns = []
                for left_ann_info, right_ann_info in zip(left_anns, right_anns):
                    left_json = left_ann_info.annotation
                    left_ann = sly.Annotation.from_json(left_json, META1)
                    right_json = right_ann_info.annotation
                    right_ann = sly.Annotation.from_json(right_json, META2)

                    tags = None
                    if state["mergeTags"] == "combine":
                        tags = left_ann.img_tags.merge(right_ann.img_tags)
                    elif state["mergeTags"] == "use left":
                        tags = left_ann.img_tags
                    elif state["mergeMetadata"] == "use right":
                        tags = right_ann.img_tags
                    if tags is None:
                        raise RuntimeError("Merge image tags: failed")
                    # drop tags that are not in result meta
                    filtered_tags = []
                    for tag in tags:
                        tag: sly.Tag
                        if res_meta.get_tag_meta(tag.meta.name) is not None:
                            filtered_tags.append(tag)
                    tags = sly.TagCollection(filtered_tags)

                    labels = None
                    if state["mergeLabels"] == "combine":
                        labels = left_ann.labels + right_ann.labels
                    elif state["mergeLabels"] == "use left":
                        labels = left_ann.labels
                    elif state["mergeLabels"] == "use right":
                        labels = right_ann.labels
                    if labels is None:
                        raise RuntimeError("Merge labels: failed")
                    # drop labels that are not in result meta
                    filtered_labels = []
                    for label in labels:
                        label: sly.Label
                        if res_meta.get_obj_class(label.obj_class.name) is not None:
                            filtered_labels.append(label)
                    labels = filtered_labels

                    res_ann = left_ann.clone(labels=labels, img_tags=tags)
                    anns.append(res_ann)

                # upload annotations
                api.annotation.upload_anns(res_image_ids, anns)

            elif message == "conflicts":
                #["unify", "intersect"]
                if state["merge"] == "intersect":
                    _increment_progress(api, task_id, progress)
                    continue
                if state["resolve"] == "skip image":
                    _increment_progress(api, task_id, progress)
                    continue
                elif state["resolve"] == "use left":
                    res_dataset = _add_simple(res_dataset, images, left_ds)
                elif state["resolve"] == "use right":
                    res_dataset = _add_simple(res_dataset, images, right_ds)
            elif message == "unique (left)":
                res_dataset = _add_simple(res_dataset, images, left_ds)
            elif message == "unique (right)":
                res_dataset = _add_simple(res_dataset, images, right_ds)

        _increment_progress(api, task_id, progress)

    fields = [
        {"field": "data.createdProjectId", "payload": result_project.id},
        {"field": "data.createdProjectName", "payload": result_project.name},
    ]
    api.app.set_fields(task_id, fields)
    app_logger.info("Project is created", extra={'project_id': result_project.id, 'project_name': result_project.name})
    #api.task.set_output_project(task_id, res_project.id, res_project.name)
    my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={
        "TEAM_ID": TEAM_ID,
        "WORKSPACE_ID": WORKSPACE_ID,
    })
    data, state = init_ui(my_app.public_api, my_app.task_id, my_app.logger)
    my_app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)