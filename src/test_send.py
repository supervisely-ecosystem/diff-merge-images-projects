import os
import json
import supervisely_lib as sly
from supervisely_lib.worker_proto import worker_api_pb2 as api_proto
from supervisely_lib.worker_api.agent_rpc import send_from_memory_generator

my_app = sly.AppService()


def _send_data(out_msg, req_id, logger):
    logger.info('Will send output data.', extra={"request_id": req_id})
    out_bytes = json.dumps(out_msg).encode('utf-8')
    my_app.api.put_stream_with_data('SendGeneralEventData',
                                    api_proto.Empty,
                                    send_from_memory_generator(out_bytes, 1048576),
                                    addit_headers={'x-request-id': req_id})
    logger.info('Output data is sent.', extra={"request_id": req_id})


@my_app.callback("merge")
@sly.timeit
def merge(api: sly.Api, task_id, context, state, app_logger):
    req_id = context.get("request_id", "abc")
    _send_data({"a": "1", "b": 2}, req_id, app_logger)


def main():
    sly.logger.info("Script arguments", extra={})
    my_app.run()


if __name__ == "__main__":
    sly.main_wrapper("main", main)