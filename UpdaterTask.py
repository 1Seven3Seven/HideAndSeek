from typing import Any

from UpdaterTaskTypes import UpdaterTaskTypes


class UpdaterTask:
    """
    A task created by a ClientHandler class pertaining information about a task to be executed by an updater.
    Contains both the task type and the data for said task.
    """

    def __init__(self, task: UpdaterTaskTypes, *data: Any):
        self.task: UpdaterTaskTypes = task
        self.data: tuple = data
