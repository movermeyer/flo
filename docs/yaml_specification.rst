.. _flo.yaml-specification:

flo.yaml specification
~~~~~~~~~~~~~~~~~~~~~~

Individual analysis tasks are defined as `YAML objects
<http://en.wikipedia.org/wiki/YAML#Associative_arrays>`__ in a file
named ``flo.yaml`` (or :ref:`whatever you prefer <flo-config>`) with
something like this:

.. code-block:: yaml

    ---
    creates: "path/to/some/output/file.txt"
    depends: "path/to/some/script.py"
    command: "python {{depends}} > {{creates}}"

Every YAML object that defines a task must have :ref:`yaml-creates`
and :ref:`yaml-command` keys and can optionally contain a
:ref:`yaml-depends` key. The order of these keys does not matter; the
above order is chosen for explanatory purposes only.

.. _yaml-creates:

creates
'''''''

The ``creates`` key uniquely identifies the resource that is
created. By default, it is interpreted as a path to a file (relative
paths are interpreted as relative to the ``flo.yaml`` file) or a
directory. Importantly, every task is intended to create a single file
or directory. If you have a task that creates multiple files, you can
either (i) split that into separate tasks or (ii) have all of those
files embedded in a directory and use the directory name as the
``creates`` value like this:

.. code-block:: yaml

   ---
   creates: "path/to/output/directory"
   depends: "path/to/some/script.py"
   command:
     - "mkdir -p {{creates}}"
     - "python {{depends}} {{creates}}"

In this case, the directory ``path/to/output/directory`` is passed as
the first argument to ``path/to/some/script.py``, which can then add
as many files as necessary to that directory. When this task is
complete, ``flo`` checks the hash of all files in
``path/to/output/directory`` and all of its child directories to
determine if it is in sync or not.

..
   You can also specify a
   protocol, such as ``mysql:database/table`` (`yet-to-be-implemented
   <http://github.com/deanmalmgren/flo/issues/15>`__), for non-file based
   resources.

.. _yaml-depends:

depends
'''''''

The ``depends`` key defines the resource(s) on which this task depends.
It is common for ``depends`` to specify many things, including data
analysis scripts or other tasks from within the ``flo.yaml``. Multiple
dependencies can be defined in a `YAML
list <http://en.wikipedia.org/wiki/YAML#Lists>`__ like this:

.. code-block:: yaml

    depends:
      - "path/to/some/script.py"
      - "another/task/creates/target.txt"

These dependencies are what ``flo`` uses to determine if a task is out
of sync and needs to be re-executed. Importantly, ``flo`` obeys the
dependencies when it constructs the task graph but always runs in a
:ref:`deterministic order <deterministic-order>`. If a specified
``depends`` does not exist immediately prior to ``flo`` running the
task, ``flo`` throws an informative error.

.. _yaml-command:

command
'''''''

The ``command`` key is mandatory and it defines the command(s) that
should be executed to produce the resource specified by the
``creates`` key. Like the ``depends`` key, multiple steps can be
defined in a `YAML list <http://en.wikipedia.org/wiki/YAML#Lists>`__
like this:

.. code-block:: yaml

    command:
      - "mkdir -p $(dirname {{creates}})"
      - "python {{depends}} > {{creates}}"

.. _yaml-templating-variables:

templating variables
''''''''''''''''''''

Importantly, the ``command`` is rendered as a `jinja
template <http://jinja.pocoo.org/>`__ to avoid duplication of
information that is already defined in that task. Its quite common to
use ``{{depends}}`` and ``{{creates}}`` in the ``command``
specification, but you can also use other variables like this:

.. code-block:: yaml

    ---
    creates: "path/to/some/output/file.txt"
    sigma: "2.137"
    depends: "path/to/some/script.py"
    command: "python {{depends}} {{sigma} > {{creates}}"

In the aforementioned example, ``sigma`` is only available when
rendering the jinja template for that task. If you'd like to use
``sigma`` in several other tasks, you can alternatively put it in a
global namespace in a flo.yaml like this (`similar example here <http://github.com/deanmalmgren/flo/blob/master/examples/model-correlations>`__):

.. code-block:: yaml

    ---
    sigma: "2.137"
    tasks: 
      - 
        creates: "path/to/some/output/file.txt"
        depends: "path/to/some/script.py"
        command: "python {{depends}} {{sigma} > {{creates}}"
      -
        creates: "path/to/another/output/file.txt"
        depends:
          - "path/to/another/script.py"
          - "path/to/some/output/file.txt"
        command: "python {{depends[0]}} {{sigma}} < {{depends[1]}} > {{creates}}"

Another common use case for global variables is when you have several
tasks that all depend on the same file. You can also use jinja
templating in the ``creates`` and ``depends`` attributes of your
``flo.yaml`` like this:

.. code-block:: yaml

    ---
    input: "data/sp500.html"
    tasks:
      -
        creates: "{{input}}"
        command:
          - "mkdir -p $(dirname {{creates}})"
          - "wget http://en.wikipedia.org/wiki/List_of_S%26P_500_companies -O {{creates}}"
      -
        creates: "data/names.dat"
        depends:
          - "src/extract_names.py"
          - "{{input}}"
        command: "python {{depends|join(' ')}} > {{creates}}"
      -
        creates: "data/symbols.dat"
        depends:
          - "src/extract_symbols.py"
          - "{{input}}"
        command: "python {{depends|join(' ')}} > {{creates}}"

There are several `examples
<http://github.com/deanmalmgren/flo/blob/master/examples/>`__ for more
inspiration on how you could use the flo.yaml specification. If you
have suggestions for other ideas, please `add them
<http://github.com/deanmalmgren/flo/issues>`__!

.. _deterministic-order:

deterministic execution order
'''''''''''''''''''''''''''''

``flo`` is *guaranteed to run in the exact same order every single
time* and its important that users understand how it works. When
``flo`` is :ref:`executed <flo-run>`, it makes sure to
obey the dependencies specified in the YAML configuration. In the
event of ties ``flo`` is executed in the same order as the tasks
appear in the YAML configuration. Technically, this is very similar to
a `breadth first search
<http://en.wikipedia.org/wiki/Breadth-first_search>`__ originating
from the set of tasks that have no dependencies except that we order
things based on the *maximum* distance that each task is from any
given source node and we break ties based on the order in the YAML
configuration file.

The `deterministic order example
<http://github.com/deanmalmgren/flo/blob/master/examples/deterministic-order>`__
contains a few different YAML configuration files to demonstrate how
this works in practice, the highlights of which are summarized here.

.. image:: ../examples/deterministic-order/sketches/sibling.png
   :alt: task graph for sibling tasks that all depend on the same parent
   :width: 200px
   :align: left

For sibling tasks, sibling tasks are executed in the order in which
they appear in the YAML configuration file, but always after the their
dependencies have been satisfied. In `this example
<http://github.com/deanmalmgren/flo/blob/master/examples/deterministic-order/sibling.yaml>`__, 
the task graph looks like this and the tasks are guaranteed to run in
alphabetical order.

.. raw:: html

   <div class="clearfix"></div>

.. image:: ../examples/deterministic-order/sketches/parallel.png
   :alt: task graph for parallel task threads
   :width: 200px
   :align: left

For parallel threads, task threads are executed based on their
distance from the source tasks and secondarily based on their ordering
in the YAML configuration file. In `this example
<http://github.com/deanmalmgren/flo/blob/master/examples/deterministic-order/parallel.yaml>`__,
the task graph looks something like this and the tasks are guaranteed
to run in alphabetical order.

.. raw:: html

   <div class="clearfix"></div>

.. image:: ../examples/deterministic-order/sketches/merge.png
   :alt: task graph for merging task threads
   :width: 200px
   :align: left

For merging task graphs, tasks are executed based on their maximal
distance from any source task. In `this example
<http://github.com/deanmalmgren/flo/blob/master/examples/deterministic-order/merge.yaml>`__,
the task graph looks something like this and the tasks are guaranteed to
run in alphabetical order.

.. raw:: html

   <div class="clearfix"></div>
