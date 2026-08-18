.. _parallel-computing:


Parallel Computing
==================

.. questions::

   - What is the Global Interpreter Lock in Python?
   - How can Python code be parallelised?

.. objectives::

   - Become familiar with different types of parallelism 
   - Learn the basics of parallel workflows, multiprocessing and distributed memory parallelism

.. instructor-note::

   - 40 min teaching/type-along
   - 40 min exercises


Modes of parallelism
--------------------

The performance of a single CPU core has stagnated over the last ten years
and most of the speed-up in scientific computing is coming from using
multiple CPU cores, i.e. parallel processing. Parallel processing can be
roughly catergorized into the following modes: 

- **Shared memory parallelism (multithreading):** 
 
  - Parallel threads do separate work
  - Different threads communicate via the same memory and write to shared variables


- **Distributed memory parallelism (multiprocessing):** 

  - Different processes manage their own memory segments
  - Different processes share data by communicating e.g. using Message Passing Interface when needed


.. note::

   **"Embarrassingly" parallel**: If you can run multiple instances of a program and do not need to synchronize/communicate with other instances, 
   i.e. the problem at hand can be easily decomposed into independent tasks or datasets and there is no need to control access to shared resources, 
   it is known as an embarrassingly parallel program. A few examples are listed here:
     - Monte Carlo analysis
     - Ensemble calculations of numerical weather prediction
     - Discrete Fourier transform 
     - Convolutional neural networks
     - Applying same model on multiple datasets


In the Python world, it is common to see the word `concurrency` denoting any type of simultaneous 
processing, including *threads*, *tasks* and *processes*. 
  - Concurrent tasks can be executed in any order but with the same final results
  - Concurrent tasks can be but need not to be executed in parallel
  - ``concurrent.futures`` module provides implementation of thread and process-based executors for managing resources pools for running concurrent tasks
  - Concurrency is difficult: Race condition and Deadlock may arise in concurrent programs

.. warning::

   Parallel programming requires that we adopt a different mental model compared to serial programming. 
   Many things can go wrong and one can get unexpected results or difficult-to-debug 
   problems. It is important to understand the possible pitfalls before embarking 
   on code parallelisation. For an entertaining take on this, see 
   `Raymond Hettinger's PyCon2016 presentation <https://www.youtube.com/watch?v=Bv25Dwe84g0>`__.


The Global Interpreter Lock (GIL)
---------------------------------

The designers of the Python language made the choice
that **only one thread in a process can run actual Python code**
by using the so-called **global interpreter lock (GIL)**.
This means that multiple threads executing Python code at the same time is prevented,
and therefore it is bad for parallelism. The main reason is that
part of the Python implementation related to the memory management is not thread-safe.
Moreover, library developers often care a lot about performance and will design APIs
that support working around the GIL. These workaround frequently lead to APIs
that are more difficult to use. Consequently, users of these APIs may experience
the GIL as a usability issue and not just a performance issue.

Starting with the 3.13 release, CPython has support for a build of Python
called free threading where the global interpreter lock (GIL) is disabled.
Free-threaded execution allows for full utilization of the available
processing power by running threads in parallel on available CPU cores.
While not all software will benefit from this automatically,
programs designed with threading in mind will run faster on multi-core hardware.

.. note::

   While the performance gains are exciting, moving to a GIL-free world requires
   a shift in mindset and an awareness of the new challenges. The biggest hurdle
   for the adoption of free-threaded Python is the vast ecosystem of existing packages. 
   Most pure Python code that is already thread-safe should work without modification.
   However, many C extensions were built with the assumption that the GIL exists,
   implicitly protecting them from certain types of race conditions. Running these
   in a free-threaded environment can lead to crashes and data corruption.
   
   The free-threaded build of CPython aims to provide similar thread-safety behavior
   to the default GIL-enabled build. Built-in types like `dict`, `list`, and `set`
   use internal locks to protect against concurrent modifications in ways that
   behave similarly to the GIL. However, Python has not historically
   guaranteed specific behavior for concurrent modifications to these built-in types,
   so this should be treated as a description of the current implementation,
   not a guarantee of current or future behavior. It's recommended to explicitly use the
   locking mechanisms (e.g. `threading.Lock` or other synchronization primitives)
   instead of relying on the internal locks of built-in types, whenever possible
   to protect shared, mutable state in the code to ensure logical correctness.
   Race conditions that once were theoretical may happen now.




Multithreading
--------------

The `threading library <https://docs.python.org/dev/library/threading.html#>`__ 
provides an API for creating and working with threads. The simplest approach to 
create and manage threads is to use the ``ThreadPoolExecutor`` class from ``concurrent.futures`` module. 
An example use case could be to download data from multiple websites using 
multiple threads:

.. code-block:: python

   import concurrent.futures

   def download_all_sites(sites):
       with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
           executor.map(my_download_function, sites)
  
The speedup gained from multithreading I/O bound problems can be understood from the following image.

.. figure:: img/Threading.png
  :align: center
  :scale: 50 %

  From https://realpython.com/, distributed via a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported licence

Further details on threading in Python can be found in the **See also** section below.


Multiprocessing
---------------

The ``multiprocessing`` module in Python supports spawning processes using an API 
similar to the ``threading`` module. It effectively side-steps the GIL by using 
*subprocesses* instead of threads, where each subprocess is an independent Python 
process. One of the simplest ways to use ``multiprocessing`` is via ``Pool`` objects and 
the parallel :meth:`Pool.map` function, similarly to what we saw for multithreading above. 

.. note:: 

   ``concurrent.futures.ProcessPoolExecutor`` is actually a wrapper for 
   ``multiprocessing.Pool`` to unify the threading and process interfaces.


Multiple arguments
^^^^^^^^^^^^^^^^^^

For functions that take multiple arguments one can instead use the :meth:`Pool.starmap`
function, and there are other options as well, see below:

.. tabs::
 
   .. tab:: ``pool.starmap``

      .. code-block:: python
         :emphasize-lines: 6,8

         import multiprocessing as mp
   
         def power_n(x, n):
             return x ** n

         if __name__ == '__main__':
             with mp.Pool(processes=4) as pool:
                 res = pool.starmap(power_n, [(x, 2) for x in range(20)])
             print(res)

   .. tab:: function adapter

      .. code-block:: python
         :emphasize-lines: 6,7,13

         from concurrent.futures import ProcessPoolExecutor

         def power_n(x, n):
             return x ** n

         def f_(args):
             return power_n(*args)

         xs = np.arange(10)
         chunks = np.array_split(xs, xs.shape[0]//2)

         with ProcessPoolExecutor(max_workers=4) as pool:
             res = pool.map(f_, chunks)
         print(list(res))


   .. tab:: multiple argument iterables

      .. code-block:: python
         :emphasize-lines: 7
            
         from concurrent.futures import ProcessPoolExecutor

         def power_n(x, n):
             return x ** n

         with ProcessPoolExecutor(max_workers=4) as pool:
             res = pool.map(power_n, range(0,10,2), range(1,11,2))
         print(list(res))
   

.. callout:: Interactive environments

   Functionality within multiprocessing requires that the ``__main__`` module be 
   importable by children processes. This means that some functions may not work 
   in the interactive interpreter like Jupyter-notebook. 

``multiprocessing`` has a number of other methods which can be useful for certain 
use cases, including ``Process`` and ``Queue`` which make it possible to have direct 
control over individual processes. Refer to the `See also`_ section below for a list 
of external resources that cover these methods.

At the end of this episode you can turn your attention back to the word-count problem 
and practice using ``multiprocessing`` pools of processes.


Exercises
---------

.. exercise:: I/O-bounded process

   In this exercise, we will download Global Forecast System (GFS) weather model data
   directly through NOAA's real-time NOMADS server.

   .. tabs::
 
      .. tab:: Multithreading

         .. literalinclude:: example/download_gfs_mt.py
	    :language: python

      .. tab:: Multiprocessing
	       
	 .. literalinclude:: example/download_gfs_mp.py
            :language: python



.. exercise:: Database

   In this exercise, we will simultaneously insert into and read from a DuckDB database
   across multiple Python threads.

   .. literalinclude:: example/duckdb_mt.py
      :language: python


.. exercise:: I/O-bound vs CPU-bound

   In this exercise, we will simulate an I/O-bound process uing the :meth:`sleep` function. 
   Typical I/O-bounded processes are disk accesses, network requests etc.

   .. literalinclude:: example/io_bound.py
      :language: python

   When the problem is compute intensive:

   .. literalinclude:: example/cpu_bound.py
      :language: python


.. exercise:: Race condition

   Race condition is considered a common issue for multi-threading/processing applications, 
   which occurs when two or more threads attempt to access the shared data and 
   try to modify it at the same time. Try to run the example using different number ``n`` to see the differences.
   Think about how we can solve this problem.


   .. literalinclude:: example/race.py
      :language: python

   .. solution::

      - locking resources: explicitly using locks
      - duplicating resources: making copys of data to each threads/processes so that they do not need to share

      .. tabs::
 
         .. tab:: locking

            .. literalinclude:: exercise/race_lock.py
               :language: python
               :emphasize-lines: 2,4,8,10

         .. tab:: duplicating

            .. literalinclude:: exercise/race_dup.py
               :language: python


.. exercise:: Compute numerical integrals

   The primary objective of this exercise is to compute integrals :math:`\int_0^1 x^{3/2} \, dx` numerically. 
   One approach to integration is by establishing a grid along the x-axis. Specifically, the integration range 
   is divided into 'n' segments or bins. Below is a basic serial code.

   .. literalinclude:: exercise/1d_Integration_serial.py

   Think about how to parallelize the code using multithreading and multiprocessing.

   .. solution:: Full source code

      .. literalinclude:: exercise/1d_Integration_multithreading.py

      .. literalinclude:: exercise/1d_Integration_multiprocessing.py


.. _See also:


See also
--------

- `More on the global interpreter lock
  <https://wiki.python.org/moin/GlobalInterpreterLock>`__
- `RealPython concurrency overview <https://realpython.com/python-concurrency/>`__
- `RealPython threading tutorial <https://realpython.com/intro-to-python-threading/>`__
- Parallel programming in Python with multiprocessing, 
  `part 1 <https://www.kth.se/blogs/pdc/2019/02/parallel-programming-in-python-multiprocessing-part-1/>`__
  and `part 2 <https://www.kth.se/blogs/pdc/2019/03/parallel-programming-in-python-multiprocessing-part-2/>`__
- Parallel programming in Python with mpi4py, `part 1 <https://www.kth.se/blogs/pdc/2019/08/parallel-programming-in-python-mpi4py-part-1/>`__
  and `part 2 <https://www.kth.se/blogs/pdc/2019/11/parallel-programming-in-python-mpi4py-part-2/>`__
- `ipyparallel documentation <https://ipyparallel.readthedocs.io/en/latest/>`__
- `IPython Parallel in 2021 <https://blog.jupyter.org/ipython-parallel-in-2021-2945985c032a>`__
- `ipyparallel tutorial <https://github.com/DaanVanHauwermeiren/ipyparallel-tutorial>`__

.. keypoints::

   - Beaware of GIL and its impact on performance
   - Use threads for I/O-bound tasks and multiprocessing for compute-bound tasks
   - Make it right before trying to make it fast
