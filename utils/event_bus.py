class EventBus:
    def __init__(self):
        self._handlers = {}

    def subscribe(self, event_name: str, handler):
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler=None):
        if event_name not in self._handlers:
            return
        if handler is None:
            self._handlers[event_name] = []
        else:
            try:
                self._handlers[event_name].remove(handler)
            except ValueError:
                pass

    def publish(self, event_name: str, *args, **kwargs):
        for handler in list(self._handlers.get(event_name, [])):
            try:
                handler(*args, **kwargs)
            except Exception as e:
                # Limpieza: antes se tragaba silencioso; un handler roto
                # (Tiendita/Ventas/Matrícula/Dashboard) debe verse en el log.
                try:
                    from utils.logger import logger
                    logger.warning(f"event_bus '{event_name}': handler falló: {e}")
                except Exception:
                    pass


# Singleton por defecto. Las vistas hacen `from utils import event_bus`
# lo que importa este MÓDULO, por eso se exponen funciones a nivel módulo.
_default_bus = EventBus()
event_bus = _default_bus


def subscribe(event_name: str, handler):
    return _default_bus.subscribe(event_name, handler)


def unsubscribe(event_name: str, handler=None):
    return _default_bus.unsubscribe(event_name, handler)


def publish(event_name: str, *args, **kwargs):
    return _default_bus.publish(event_name, *args, **kwargs)