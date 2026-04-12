from cinder.scheduler import weights

class PerformanceWeigher(weights.BaseHostWeigher):

    def _weigh_object(self, host_state, weight_properties):

        host = host_state.host
        backend = host.split('@')[1]

        print(f">>> [PLUGIN] HOST: {host}")
        print(f">>> [PLUGIN] BACKEND: {backend}")

        return 1.0