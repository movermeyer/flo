"""Base resource here
"""

import hashlib

class BaseResource(object):
    """A resource is any `creates` or `depends` or `task` that is
    mentioned in a workflow.yaml. A resource can be on the file
    system, in a database, etc.

    The basic functionality of an resource is to assess the state of the
    resource and whether it is in sync. 
    """

    def __init__(self, graph, name):
        self.graph = graph
        self.name = name
        
        # add this resource to the graph's resource_dict, which globally
        # stores all of the resources associated with this workflow
        if self.graph.resource_dict.has_key(name):
            raise ValueError("Resource '%s' already exists in this graph" % name)
        self.graph.resource_dict[name] = self

    def __repr__(self):
        return self.name + ':' + str(id(self))

    @property
    def root_directory(self):
        """Easy access to the graph's root_directory, which is stored once for
        every task"""
        return self.graph.root_directory

    def _get_stream_state(self, stream, block_size=2**20):
        """Read in a stream in relatively small `block_size`s to make sure we
        won't have memory problems on BIG DATA streams.
        http://stackoverflow.com/a/1131255/564709
        """
        state = hashlib.sha1()
        while True:
            data = stream.read(block_size)
            if not data:
                break
            state.update(data)
        return state.hexdigest()

    @property
    def previous_state(self):
        """Get the previous state of this resource prior to this run. If the
        resource does not exist, throw an error.
        """
        return self.graph.get_state_from_storage(self.name)

    @property
    def current_state(self):
        """Get the current state of this resource. If the resource does
        not exist, throw an error.
        
        This method must be overwritten by any child classes.

        TODO: need to figure out a way to avoid running this method
        multiple times on the same resource during a single workflow
        run. this is more of a performance issue that can be revisited
        later as it becomes an issue. can maybe cache somehow?
        """
        raise NotImplementedError(
            "Must implement current_state for child classes"
        )
        
    def state_in_sync(self):
        """Check the stored state of this resource compared with the current
        state of this resource. If they are the same, then this resource
        is in_sync.
        """
        return self.previous_state == self.current_state
