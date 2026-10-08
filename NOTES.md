== curl ==
# GET  /api/containers
# GET  /api/containers/api/stats?minutes=60
# GET  /api/containers/api/logs?tail=100
# POST /api/alerts  {"container":"api","metric":"cpu","threshold":90,"notify":"telegram"}
# GET  /api/alerts
# GET  /api/stream   (SSE)

== session plan ==
# Session 1: collector (mock docker) + history → tests
# Session 2: alerts + api → tests
# Session 3: web (SSE cards + charts) → screenshots → README → CI/Docker/Pages → tag
