__author__ = "Brian Schkerke"
__copyright__ = "Copyright 2016 Brian Schkerke"
__license__ = "MIT"


class Events(object):
    """
        The bare minimum of a static event handler.  Allows for global registration
        of callbacks to events as defined solely by string IDs.  The event handlers
        should have the function event_handler(object_type); the only argument passed
        to the callback is the object which instantiated the event.
    """
    _callbacks = None

    @staticmethod
    def on(event_name, callback):
        """
            Subscribes to an event.

        :param event_name: The name of the event to create a subscription for.
        :param callback: The function to be invoked when the event is triggered.
        :return: None
        :rtype: None
        """

        if Events._callbacks is None:
            Events._callbacks = {}

        if event_name not in Events._callbacks:
            Events._callbacks[event_name] = [callback]
        else:
            Events._callbacks[event_name].append(callback)

    @staticmethod
    def trigger(event_name, callback_argument):
        """
            Triggers the specified event (as specified by event_name).

        :param callback_argument:  The argument to be passed to the subscribed functions.
        :param event_name:  The string name of the event being triggered.
        :return: None
        :rtype: None
        """
        if Events._callbacks is not None and event_name in Events._callbacks:
            for callback in Events._callbacks[event_name]:
                callback(callback_argument)
