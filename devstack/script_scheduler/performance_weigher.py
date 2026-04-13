from oslo_log import log as logging
from cinder.scheduler import weights

LOG = logging.getLogger(__name__)

class PerformanceWeigher(weights.BaseHostWeigher):

    def _weigh_object(self, host_state, weight_properties):
        """
        Questo metodo viene chiamato per ogni backend disponibile.
        Deve restituire un valore numerico (peso).
        """
        host = host_state.host
        # Estraiamo il nome del backend (es. low_cap#LVM_BACKEND_1)
        backend = host.split('@')[1] if '@' in host else host

        # Recuperiamo i dati sulle performance
        free_space = host_state.free_capacity_gb

        # --- LOG PER IL DEBUG ---
        LOG.info(">>> [PerformanceWeigher] Analisi Backend: %s", backend)
        LOG.info(">>> [PerformanceWeigher] Spazio Libero rilevato: %s GB", free_space)

        weight = float(free_space)
        
        LOG.info(">>> [PerformanceWeigher] Peso assegnato a %s: %f", backend, weight)

        return weight