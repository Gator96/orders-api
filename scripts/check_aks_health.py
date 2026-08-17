import json
import os
import subprocess
import sys


def get_pods(namespace, label):
    command = [
        "kubectl",
        "get",
        "pods",
        "-n",
        namespace,
        "-l",
        f"app={label}",
        "-o",
        "json"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    return json.loads(result.stdout)


def check_health(pod_data):
    pods = pod_data.get("items", [])

    if not pods:
        print("CRITICAL: No matching pods found")
        return False

    all_healthy = True

    for pod in pods:
        name = pod["metadata"]["name"]
        phase = pod["status"].get("phase", "Unknown")

        container_statuses = pod["status"].get(
            "containerStatuses",
            []
        )

        containers_ready = (
            len(container_statuses) > 0
            and all(
                container.get("ready", False)
                for container in container_statuses
            )
        )

        if phase == "Running" and containers_ready:
            print(f"OK: {name} is Running and Ready")
        else:
            print(
                f"CRITICAL: {name} "
                f"phase={phase}, ready={containers_ready}"
            )
            all_healthy = False

    return all_healthy


def main():
    namespace = os.getenv("NAMESPACE", "sre-lab")
    app_label = os.getenv("APP_LABEL", "orders-api")

    print(
        f"Checking application '{app_label}' "
        f"in namespace '{namespace}'"
    )

    try:
        pod_data = get_pods(namespace, app_label)

        healthy = check_health(pod_data)

        if healthy:
            print("Application health check PASSED")
            sys.exit(0)

        print("Application health check FAILED")
        sys.exit(1)

    except subprocess.CalledProcessError as error:
        print(f"kubectl command failed: {error.stderr}")
        sys.exit(2)

    except FileNotFoundError:
        print("kubectl is not installed or not in PATH")
        sys.exit(3)

    except json.JSONDecodeError:
        print("Unable to parse kubectl JSON output")
        sys.exit(4)

    except Exception as error:
        print(f"Unexpected error: {error}")
        sys.exit(5)


if __name__ == "__main__":
    main()
