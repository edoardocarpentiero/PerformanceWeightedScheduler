from oslo_log import log as logging
from cinder.scheduler import weights

LOG = logging.getLogger(__name__)

class PerformanceWeigher(weights.BaseHostWeigher):

    def weigh_multiplier(self) -> float:
        return 1.0
        
    def _weigh_object(self, host_state, weight_properties):
        host = host_state.host
        backend = host.split('@')[1] if '@' in host else host

        free_space = host_state.free_capacity_gb

        LOG.info(">>> [PerformanceWeigher] Analisi Backend: %s", backend)
        LOG.info(">>> [PerformanceWeigher] Spazio Libero: %s GB", free_space)

        weight = float(free_space)

        LOG.info(">>> [PerformanceWeigher] Peso assegnato a %s: %f", backend, weight)

        return weight