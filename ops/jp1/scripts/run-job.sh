#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# JP1 standard launcher script for KOIKI Batch apps.
# - Invoked by JP1/AJS
# - Validates required arguments
# - Loads environment and job parameter files
# - Executes Spring Batch app jar
# - Maps exit codes for JP1 decisioning
# -----------------------------------------------------------------------------

usage() {
  cat <<USAGE
Usage:
  $0 -j <job_name> -e <env> -a <jar_path> [-p <yyyymmdd>] [-r <request_id>] [-x <extra_args>]

Required:
  -j  Job name (e.g. customer-daily-sync)
  -e  Environment key (dev|stg|prd)
  -a  Executable jar path (e.g. /opt/koiki/apps/customer-a-batch-app.jar)

Optional:
  -p  Business date (YYYYMMDD). Defaults to today's date.
  -r  Request id / operation id. Defaults to auto-generated value.
  -x  Extra Spring arguments (quoted string)
USAGE
}

JOB_NAME=""
ENV_KEY=""
JAR_PATH=""
BIZ_DATE="$(date +%Y%m%d)"
REQUEST_ID="JP1-$(date +%Y%m%d%H%M%S)"
EXTRA_ARGS=""

while getopts ":j:e:a:p:r:x:h" opt; do
  case "${opt}" in
    j) JOB_NAME="${OPTARG}" ;;
    e) ENV_KEY="${OPTARG}" ;;
    a) JAR_PATH="${OPTARG}" ;;
    p) BIZ_DATE="${OPTARG}" ;;
    r) REQUEST_ID="${OPTARG}" ;;
    x) EXTRA_ARGS="${OPTARG}" ;;
    h)
      usage
      exit 0
      ;;
    :) echo "[ERROR] Option -${OPTARG} requires an argument." >&2; usage; exit 30 ;;
    \?) echo "[ERROR] Invalid option: -${OPTARG}" >&2; usage; exit 30 ;;
  esac
done

if [[ -z "${JOB_NAME}" || -z "${ENV_KEY}" || -z "${JAR_PATH}" ]]; then
  echo "[ERROR] Missing required options." >&2
  usage
  exit 30
fi

if [[ ! "${BIZ_DATE}" =~ ^[0-9]{8}$ ]]; then
  echo "[ERROR] bizDate must be YYYYMMDD: ${BIZ_DATE}" >&2
  exit 20
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JP1_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${JP1_ROOT}/params/env/${ENV_KEY}.env"
JOB_PARAM_FILE="${JP1_ROOT}/params/job/${JOB_NAME}.properties"

if [[ ! -f "${JAR_PATH}" ]]; then
  echo "[ERROR] JAR not found: ${JAR_PATH}" >&2
  exit 30
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[ERROR] Environment file not found: ${ENV_FILE}" >&2
  exit 30
fi

if [[ ! -f "${JOB_PARAM_FILE}" ]]; then
  echo "[WARN ] Job parameter file not found; continue without it: ${JOB_PARAM_FILE}" >&2
fi

# shellcheck disable=SC1090
source "${ENV_FILE}"

LOG_DIR="${KOIKI_BATCH_LOG_DIR:-${JP1_ROOT}/logs}"
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/${JOB_NAME}_${BIZ_DATE}_$(date +%H%M%S).log"

SPRING_ARGS=(
  "--spring.profiles.active=${ENV_KEY}"
  "--job.name=${JOB_NAME}"
  "--job.requestId=${REQUEST_ID}"
  "--job.bizDate=${BIZ_DATE}"
)

if [[ -f "${JOB_PARAM_FILE}" ]]; then
  SPRING_ARGS+=("--job.config=${JOB_PARAM_FILE}")
fi

if [[ -n "${EXTRA_ARGS}" ]]; then
  # shellcheck disable=SC2206
  EXTRA_ARR=(${EXTRA_ARGS})
  SPRING_ARGS+=("${EXTRA_ARR[@]}")
fi

START_TS="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[INFO ] START ${START_TS} job=${JOB_NAME} env=${ENV_KEY} requestId=${REQUEST_ID} bizDate=${BIZ_DATE}" | tee -a "${LOG_FILE}"

set +e
java -jar "${JAR_PATH}" "${SPRING_ARGS[@]}" >> "${LOG_FILE}" 2>&1
APP_RC=$?
set -e

END_TS="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[INFO ] END   ${END_TS} job=${JOB_NAME} env=${ENV_KEY} requestId=${REQUEST_ID} appRc=${APP_RC}" | tee -a "${LOG_FILE}"

# Exit code mapping for JP1
# 0: normal
# 10: warning / partial success
# 20: business error (retry may depend on business condition)
# 30: system error (infra/app failure)
case "${APP_RC}" in
  0)  JP1_RC=0 ;;
  10) JP1_RC=10 ;;
  20) JP1_RC=20 ;;
  *)  JP1_RC=30 ;;
esac

echo "[INFO ] JP1_RC=${JP1_RC} (from APP_RC=${APP_RC}) log=${LOG_FILE}" | tee -a "${LOG_FILE}"
exit "${JP1_RC}"
