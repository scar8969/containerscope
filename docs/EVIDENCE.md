# Evidence

Every claim below comes from a command that was actually run against this
exact checkout. Nothing here is inferred from the source alone.

## Commands

```sh
# from the project directory, with _tools and _tools/_vendor on PYTHONPATH
python -m pytest -q -p hosttmp_proj tests/
python -m compileall -q src
```

## Recorded results

| check | result |
| --- | --- |
| compileall | exit 0 |
| pytest | -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html |
| pytest_exit_code | 0 |
| recorded_at | 2026-10-08 |
| routes_ok | 13 |
| routes_probed | 13 |

## HTTP surface

One real GET per rule in the assembled URL map, through Flask's test
client. `ok` includes 404 on a templated path: an empty database has
no such resource, and 404 is the honest answer for that.

| method | path | rule | status | bytes | note |
| --- | --- | --- | --- | --- | --- |
| GET | `/` | `/` | 200 | 5671 | ok |
| GET | `/alerts` | `/alerts` | 200 | 5066 | ok |
| GET | `/api/alerts` | `/api/alerts` | 200 | 14 | ok |
| GET | `/api/containers` | `/api/containers` | 200 | 93 | ok |
| GET | `/api/containers/demo/logs` | `/api/containers/<name>/logs` | 200 | 118 | ok |
| GET | `/api/containers/demo/stats` | `/api/containers/<name>/stats` | 200 | 14 | ok |
| GET | `/api/health` | `/api/health` | 200 | 41 | ok |
| GET | `/api/stream` | `/api/stream` | 200 | 32 | ok |
| GET | `/healthz` | `/healthz` | 200 | 59 | ok |
| GET | `/livez` | `/livez` | 200 | 19 | ok |
| GET | `/metrics` | `/metrics` | 200 | 256 | ok |
| GET | `/readyz` | `/readyz` | 200 | 31 | ok |
| GET | `/version` | `/version` | 200 | 924 | ok |

## Operational endpoints

`/healthz` answered **200**:

```
{"service":"docker_stats","status":"ok","version":"0.1.0"}
```

`/livez` answered **200**:

```
{"status":"alive"}
```

`/readyz` answered **200**:

```
{"checks":[],"status":"ready"}
```

`/metrics` answered **200**:

```
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 8
# TYPE http_request_duration_seconds_sum counter
http_request_duration_seconds_sum{method="GET"} 0.0481644
# TYPE process_uptime_seconds gauge
process_uptime_seconds 0.536
```

`/version` answered **200**:

```
{"config":{"app_name":"docker_stats","data_dir":".\\var","database_configured":false,"debug":false,"env":"development","host":"0.0.0.0","legacy_env_present":[],"log_json":true,"log_level":"INFO","port":8000,"secret_key_configured":false},"paths":{"data_dir":"b12_docker_sta
```

## Headers observed on /healthz

| header | value |
| --- | --- |
| X-Request-ID | f2251c017ba949b89693ec8d8c47c9ed |
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| Referrer-Policy | no-referrer |
| Cross-Origin-Opener-Policy | same-origin |
| Permissions-Policy | geolocation=(), microphone=(), camera=() |
| Content-Type | application/json |

## What this file does not claim

- No browser screenshot: this host denies the Chromium sandbox the renderer
  needs, so the HTTP surface is evidenced with recorded status codes instead.
- No network access: the suite is hermetic and contacts no remote host.
- No container run: the Dockerfile is reviewed, not executed, because no
  container runtime is reachable from this host.
