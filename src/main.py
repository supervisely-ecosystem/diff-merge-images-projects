import os
import supervisely_lib as sly


my_app = sly.AppService(ignore_task_id=True)

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])

PROJECT_ID1 = int(os.environ['modal.state.projectId1'])
PROJECT1 = None
META1: sly.ProjectMeta = None

PROJECT_ID2 = int(os.environ['modal.state.projectId2'])
PROJECT2 = None
META2: sly.ProjectMeta = None

CLASSES_INFO = None
TAGS_INFO = None

RESULTS = []


def process_items(ds_info1, collection1, ds_info2, collection2):
    ds_names = ds_info1.keys() | ds_info2.keys()

    results = []
    results_data = []
    for name in ds_names:
        compare = {}
        images1 = collection1.get(name, [])
        images2 = collection2.get(name, [])
        if len(images1) == 0:
            compare["infoMessage"] = ["Not found in Project #1"]
            compare["infoIcon"] = [["zmdi zmdi-long-arrow-left", "zmdi zmdi-alert-circle-o"]]
            compare["color"] = ["#F39C12"]
            compare["left"] = None
            compare["right"] = {"name": name, "count": len(images2)}
            continue
        if len(images2) == 0:
            compare["infoMessage"] = ["Not found in Project #2"]
            compare["infoIcon"] = [["zmdi zmdi-alert-circle-o", "zmdi zmdi-long-arrow-right"]]
            compare["color"] = ["#F39C12"]
            compare["left"] = {"name": name, "count": len(images1)}
            compare["right"] = None
            continue

        img_dict1 = {img_info.name: img_info for img_info in images1}
        img_dict2 = {img_info.name: img_info for img_info in images2}

        matched = []
        diff = []  # same names but different hashes or image sizes
        same_names = img_dict1.keys() & img_dict2.keys()
        for img_name in same_names:
            dest = matched if img_dict1[img_name].hash == img_dict2[img_name].hash else diff
            dest.append((img_dict1[img_name], img_dict2[img_name]))

        uniq1 = [img_dict1[name] for name in img_dict1.keys() - same_names]
        uniq2 = [img_dict2[name] for name in img_dict2.keys() - same_names]

        compare["message"] = ["matched", "conflicts", "unique (in left)", "unique (in right)"]
        compare["icon"] = [["zmdi zmdi-check"], ["zmdi zmdi-close"], ["zmdi zmdi-plus-circle-o"], ["zmdi zmdi-plus-circle-o"]]
        compare["color"] = ["green", "red", "#20a0ff", "#20a0ff"]
        compare["numbers"] = [len(matched), len(diff), len(uniq1), len(uniq2)]
        compare["left"] = {"name": name, "count": len(images1)}
        compare["right"] = {"name": name, "count": len(images2)}

        results.append(compare)

    return results


def _get_all_images(api: sly.Api, project):
    ds_info = {}
    ds_images = {}
    for dataset in api.dataset.get_list(project.id):
        ds_info[dataset.name] = dataset
        ds_images[dataset.name] = api.image.get_list(dataset.id)
    return ds_info, ds_images


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
        # "mergeClassesOptions": ["unify", "intersect"],
        # "mergeTagsOptions": ["unify", "intersect"],
        # "resolveClassesOptions": ["skip class", "use left", "use right"],
        # "resolveTagsOptions": ["skip tag", "use left", "use right"],
        # "createdProjectId": None,
        # "createdProjectName": None
        "clickedName": ""
    }
    state = {
        "mergeClasses": "unify",
        "mergeTags": "unify",
        "resolveClasses": "skip class",
        "resolveTags": "skip tag",
        "resultProjectName": "merged project",
        "teamId": TEAM_ID,
        "workspaceId": WORKSPACE_ID
    }
    return data, state


def _merge(items_info, collection1, collection2, merge_option, resolve):
    pass
    # res = []
    # matched_items, conflict_items, missed_items = items_info
    # for info in matched_items:
    #     res.append(collection1.get(info["name1"]))
    # if merge_option == "unify":
    #     for info in conflict_items:
    #         if "skip" in resolve:
    #             continue
    #         elif resolve == "use left":
    #             res.append(collection1.get(info["name1"]))
    #         elif resolve == "use right":
    #             res.append(collection2.get(info["name2"]))
    #     for info in missed_items:
    #         if "name1" in info:
    #             res.append(collection1.get(info["name1"]))
    #         else:
    #             res.append(collection2.get(info["name2"]))
    # return res

def compare():
    pass


@my_app.callback("merge")
@sly.timeit
def merge(api: sly.Api, task_id, context, state, app_logger):
    classes = _merge(CLASSES_INFO, META1.obj_classes, META2.obj_classes, state["mergeClasses"], state["resolveClasses"])
    tags = _merge(TAGS_INFO, META1.tag_metas, META2.tag_metas, state["mergeTags"], state["resolveTags"])

    res_meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection(classes),
                               tag_metas=sly.TagMetaCollection(tags),
                               project_type=PROJECT1.type)
    res_project = api.project.create(state["workspaceId"],
                                     state["resultProjectName"],
                                     type=PROJECT1.type,
                                     description=f"{PROJECT1.name} + {PROJECT2.name}",
                                     change_name_if_conflict=True)
    api.project.update_meta(res_project.id, res_meta.to_json())
    api.project.update_custom_data(res_project.id, {
        "project1": {"id": PROJECT1.id, "name": PROJECT1.name},
        "project2": {"id": PROJECT2.id, "name": PROJECT2.name}
    })
    fields = [
        {"field": "data.createdProjectId", "payload": res_project.id},
        {"field": "data.createdProjectName", "payload": res_project.name},
    ]
    api.app.set_fields(task_id, fields)
    app_logger.info("Project is created", extra={'project_id': res_project.id, 'project_name': res_project.name})
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