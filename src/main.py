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


def process_items(collection1, collection2, diff_msg="Shape conflict"):
    items1 = {item.name: 1 for item in collection1}
    items2 = {item.name: 1 for item in collection2}
    names = items1.keys() | items2.keys()
    mutual = items1.keys() & items2.keys()
    diff1 = items1.keys() - mutual
    diff2 = items2.keys() - mutual

    match = []
    differ = []
    missed = []

    def set_info(d, index, meta):
        d[f"name{index}"] = meta.name
        d[f"color{index}"] = sly.color.rgb2hex(meta.color)
        if type(meta) is sly.ObjClass:
            d[f"shape{index}"] = meta.geometry_type.geometry_name()
            d[f"shapeIcon{index}"] = "zmdi zmdi-shape"
        else:
            meta: sly.TagMeta
            d[f"shape{index}"] = meta.value_type
            d[f"shapeIcon{index}"] = "zmdi zmdi-label"

    for name in names:
        compare = {}
        meta1 = collection1.get(name)
        if meta1 is not None:
            set_info(compare, 1, meta1)
        meta2 = collection2.get(name)
        if meta2 is not None:
            set_info(compare, 2, meta2)

        compare["infoMessage"] = "Match"
        compare["infoColor"] = "green"
        if name in mutual:
            flag = True
            if type(meta1) is sly.ObjClass and meta1.geometry_type != meta2.geometry_type:
                flag = False
            if type(meta1) is sly.TagMeta:
                meta1: sly.TagMeta
                meta2: sly.TagMeta
                if meta1.value_type != meta2.value_type:
                    flag = False
                if meta1.value_type == sly.TagValueType.ONEOF_STRING:
                    if set(meta1.possible_values) != set(meta2.possible_values):
                        diff_msg = "Type OneOf: conflict of possible values"
                    flag = False

            if flag is False:
                compare["infoMessage"] = diff_msg
                compare["infoColor"] = "red"
                compare["infoIcon"] = ["zmdi zmdi-close"],
                differ.append(compare)
            else:
                compare["infoIcon"] = ["zmdi zmdi-check"],
                match.append(compare)
        else:
            if name in diff1:
                compare["infoMessage"] = "Not found in Project #2"
                compare["infoIcon"] = ["zmdi zmdi-alert-circle-o", "zmdi zmdi-long-arrow-right"]
                compare["iconPosition"] = "right"
            else:
                compare["infoMessage"] = "Not found in Project #1"
                compare["infoIcon"] = ["zmdi zmdi-long-arrow-left", "zmdi zmdi-alert-circle-o"]
            compare["infoColor"] = "#FFBF00"
            missed.append(compare)

    table = []
    table.extend(match)
    table.extend(differ)
    table.extend(missed)
    return table, match, differ, missed


def init_ui(api: sly.Api, task_id, app_logger):
    global PROJECT1, PROJECT2, META1, META2, CLASSES_INFO, TAGS_INFO

    PROJECT1 = api.project.get_info_by_id(PROJECT_ID1)
    PROJECT2 = api.project.get_info_by_id(PROJECT_ID2)

    if PROJECT1.type != PROJECT2.type:
        raise TypeError(f"Projects have different types: {str(PROJECT1.type)} != {str(PROJECT2.type)}")

    META1 = sly.ProjectMeta.from_json(api.project.get_meta(PROJECT_ID1))
    META2 = sly.ProjectMeta.from_json(api.project.get_meta(PROJECT_ID2))

    classes_table, match_cls, differ_cls, missed_cls = process_items(META1.obj_classes, META2.obj_classes)
    CLASSES_INFO = [match_cls, differ_cls, missed_cls]

    tags_table, match_tag, differ_tag, missed_tag = process_items(META1.tag_metas, META2.tag_metas, diff_msg="Type conflict")
    TAGS_INFO = [match_tag, differ_tag, missed_tag]

    data = {
        "projectId1": PROJECT1.id,
        "projectName1": PROJECT1.name,
        "projectPreviewUrl1": api.image.preview_url(PROJECT1.reference_image_url, 100, 100),
        "projectId2": PROJECT2.id,
        "projectName2": PROJECT2.name,
        "projectPreviewUrl2": api.image.preview_url(PROJECT2.reference_image_url, 100, 100),
        "cards": [
            {
                "table": classes_table,
                "name": "Compare Classes",
                "description": "Classes colors are ignored",
                "columnSuffix": "classes"
            },
            {
                "table": tags_table,
                "name": "Compare Tags",
                "description": "Tags colors are ignored",
                "columnSuffix": "tags"
            }
        ],
        "mergeClassesOptions": ["unify", "intersect"],
        "mergeTagsOptions": ["unify", "intersect"],
        "resolveClassesOptions": ["skip class", "use left", "use right"],
        "resolveTagsOptions": ["skip tag", "use left", "use right"],
        "createdProjectId": None,
        "createdProjectName": None
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
    res = []
    matched_items, conflict_items, missed_items = items_info
    for info in matched_items:
        res.append(collection1.get(info["name1"]))
    if merge_option == "unify":
        for info in conflict_items:
            if "skip" in resolve:
                continue
            elif resolve == "use left":
                res.append(collection1.get(info["name1"]))
            elif resolve == "use right":
                res.append(collection2.get(info["name2"]))
        for info in missed_items:
            if "name1" in info:
                res.append(collection1.get(info["name1"]))
            else:
                res.append(collection2.get(info["name2"]))
    return res


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


#@TODO: readme - project custom data
#@TODO: readme - default res team/workspace == current
if __name__ == "__main__":
    sly.main_wrapper("main", main)