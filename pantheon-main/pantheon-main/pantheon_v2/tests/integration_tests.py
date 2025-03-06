import os
import json
import time
import base64


class TemporalConfig:
    def __init__(self, cert_path: str, key_path: str, namespace: str, address: str):
        self.cert_path = cert_path
        self.key_path = key_path
        self.namespace = namespace
        self.address = address


class Action:
    def __init__(self, json_data: dict):
        self.action_type = json_data["action_type"]
        self.action_name = json_data["action_name"]
        self.action_input = json_data["action_input"]

    def run(
        self, temporal_config: TemporalConfig, workflow_id: str, run_id: str
    ) -> bool:
        if self.action_type == "signal_workflow":
            signal_workflow_command = f"temporal workflow signal --workflow-id {workflow_id} --run-id {run_id} --name {self.action_name} --input '{json.dumps(self.action_input)}' --address {temporal_config.address} --namespace {temporal_config.namespace} --tls-cert-path {temporal_config.cert_path} --tls-key-path {temporal_config.key_path}"
            signal_output = os.popen(signal_workflow_command).read()
            if "Signal workflow succeeded" in signal_output:
                return True

        return False


class Test:
    workflow_name: str
    task_queue: str
    input: dict
    expected_output: dict
    actions: list[dict]

    def __init__(self, json_data: dict):
        self.workflow_name = json_data["workflow_name"]
        self.task_queue = json_data["task_queue"]
        self.input = json_data["input"]
        self.expected_output = json_data["expected_output"]
        self.actions: list[Action] = [Action(action) for action in json_data["actions"]]
        self.completed_actions = []

    def start_workflow(self, temporal_config: TemporalConfig):
        workflow_start_command = f"temporal workflow start --task-queue {self.task_queue} --type {self.workflow_name} --input '{json.dumps(self.input)}' --address {temporal_config.address} --tls-cert-path {temporal_config.cert_path} --tls-key-path {temporal_config.key_path} --namespace {temporal_config.namespace}"
        workflow_start_output = os.popen(workflow_start_command).read()
        workflow_id = (
            workflow_start_output.split("WorkflowId")[1].split("\n")[0].strip()
        )
        run_id = workflow_start_output.split("RunId")[1].split("\n")[0].strip()
        print(
            f"Started workflow {self.workflow_name} with WorkflowId {workflow_id} and RunId {run_id}"
        )
        return workflow_id, run_id

    def run_actions(
        self, temporal_config: TemporalConfig, workflow_id: str, run_id: str
    ):
        for action in self.actions:
            if action.action_name in self.completed_actions:
                continue

            action_success = action.run(temporal_config, workflow_id, run_id)
            if action_success:
                print(f"Successfully completed action {action.action_name}")
                self.completed_actions.append(action.action_name)

    def get_workflow_status(
        self, temporal_config: TemporalConfig, workflow_id: str, run_id: str
    ) -> bool:
        workflow_status_command = f"temporal workflow show --workflow-id {workflow_id} --run-id {run_id} --address {temporal_config.address} --namespace {temporal_config.namespace} --tls-cert-path {temporal_config.cert_path} --tls-key-path {temporal_config.key_path} --output json"
        workflow_status_output = os.popen(workflow_status_command).read()
        events = json.loads(workflow_status_output)["events"]
        current_state = ""
        for event in events:
            current_state = event["eventType"]
            if current_state == "EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED":
                workflow_result = event["workflowExecutionCompletedEventAttributes"][
                    "result"
                ]["payloads"]
                for result in workflow_result:
                    output = json.loads(base64.b64decode(result["data"]))
                    return output

        return None

    def run(self, temporal_config: TemporalConfig) -> bool:
        # Step 1: Start workflow
        workflow_id, run_id = self.start_workflow(temporal_config)

        # Step 2: Run actions
        self.run_actions(temporal_config, workflow_id, run_id)

        # Step 3: Check if workflow is completed
        attempt = 0
        while attempt < 10:
            output = self.get_workflow_status(temporal_config, workflow_id, run_id)
            if output is None:
                print(
                    f"Workflow {workflow_id} is not completed yet. Attempt {attempt + 1} of 10"
                )
                time.sleep(5)
                attempt += 1
                continue

            if output == self.expected_output:
                print(
                    f"Successfully matched expected output for test {self.workflow_name}"
                )
                return True
            else:
                print(f"Failed to match expected output for test {self.workflow_name}")
                break

        return False


class TestSuite:
    def __init__(self, json_data: dict):
        self.json_data = json_data
        self.tests: list[Test] = [Test(test) for test in json_data["tests"]]

    def run_tests(self, temporal_config: TemporalConfig) -> bool:
        suite_name = self.json_data["suite_name"]
        print(f"Running test suite {suite_name}")
        for test in self.tests:
            test_success = test.run(temporal_config)
            if not test_success:
                print(f"Test {test.workflow_name} failed")
                return False

        print(f"All tests in suite {suite_name} passed")
        return True


if __name__ == "__main__":
    print("Starting integration tests")
    import sys

    args = sys.argv[1:]

    temporal_config = TemporalConfig(
        cert_path=args[0], key_path=args[1], namespace=args[2], address=args[3]
    )

    # Recursively find all json files in pantheon_v2/processes
    json_files = []
    for root, dirs, files in os.walk("pantheon_v2/processes"):
        for file in files:
            if file.endswith("integration_tests.json"):
                json_files.append(os.path.join(root, file))

    print(json_files)

    for json_file in json_files:
        with open(json_file, "r") as f:
            json_data = json.load(f)

        test_suite = TestSuite(json_data)
        test_success = test_suite.run_tests(temporal_config)
        if not test_success:
            print("Test suite failed")
            exit(1)
