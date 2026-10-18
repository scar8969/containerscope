def poll():
    import docker

    client = docker.from_env()
    out = []
    for c in client.containers.list():
        stats = c.stats(stream=False)
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        sys_delta = (
            stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
        )
        cpu = cpu_delta / sys_delta * 100.0 if sys_delta else 0.0
        mem = stats["memory_stats"].get("usage", 0)
        net = stats.get("networks", {})
        net_in = sum(v.get("rx_bytes", 0) for v in net.values())
        net_out = sum(v.get("tx_bytes", 0) for v in net.values())
        out.append(
            {
                "container": c.name,
                "cpu": round(cpu, 1),
                "mem": mem,
                "net_in": net_in,
                "net_out": net_out,
                "status": c.status,
            }
        )
    return out
