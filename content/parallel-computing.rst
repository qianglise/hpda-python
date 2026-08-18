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

   .. literalinclude:: example/download_gfs_mt.py
      :language: python

   .. literalinclude:: example/download_gfs_mp.py
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

.. exercise:: Word-autocorrelation example project

   Inspired by a study of `dynamic correlations of words in written text 
   <https://www.scirp.org/journal/paperinformation.aspx?paperid=92643>`__,
   we decide to investigate autocorrelations (ACFs) of words in our database of book texts
   in the `word-count project <https://github.com/enccs/word-count-hpda>`__.
   Many of the exercises below are based on working with the following 
   word-autocorrelation code, so let us get familiar with it.

   .. solution:: Full source code

      .. literalinclude:: exercise/autocorrelation.py

   - The script takes three command-line arguments: the path of a datafile (book text), 
     the path to the processed word-count file, and the output filename for the 
     computed autocorrelation function.
   - The ``__main__`` block calls the :meth:`setup` function to preprocess the text  
     (remove delimiters etc.) and load the pre-computed word-count results.
   - :meth:`word_acf` computes the word ACF in a text for a given word using simple 
     for-loops (you will learn to speed it up later).
   - :meth:`ave_word_acf` loops over a list of words and computes their average ACF.

   To run this code for one book e.g. *pg99.txt*:

   .. code-block:: console

      $ git clone https://github.com/ENCCS/word-count-hpda.git
      $ cd word-count-hpda 
      $ python source/wordcount.py data/pg99.txt processed_data/pg99.dat
      $ python source/autocorrelation.py data/pg99.txt processed_data/pg99.dat results/acf_pg99.dat

   It will print out the time it took to calculate the ACF.      


.. exercise:: Parallelize word-autocorrelation code with multiprocessing

   A serial version of the code is available in the 
   `source/autocorrelation.py <https://github.com/ENCCS/word-count-hpda/blob/main/source/autocorrelation.py>`__
   script in the word-count repository. The full script can be viewed above, 
   but we focus on the :meth:`word_acf` and :meth:`ave_word_acf` functions:

   .. literalinclude:: exercise/autocorrelation.py
      :pyobject: word_acf
      
   .. literalinclude:: exercise/autocorrelation.py
      :pyobject: ave_word_acf

   - Think about what this code is doing and try to find a good place to parallelize it using 
     a pool of processes. 
   - With or without having a look at the hints below, try to parallelize 
     the code using ``multiprocessing`` and use :meth:`time.time()` to measure the speedup when running 
     it for one book.
   - **Note**: You will not be able to use Jupyter for this task due to the above-mentioned limitation of ``multiprocessing``.

   .. solution:: Hints
 
      The most time-consuming parts of this code is the double-loop inside 
      :meth:`word_acf` (you can confirm this in an exercise in the next episode). 
      This function is called 16 times in the :meth:`ave_word_acf`
      function, once for each word in the top-16 list. This looks like a perfect place to use a multiprocessing 
      pool of processes!

      We would like to do something like:

      .. code-block:: python

         with Pool(4) as p:
             results = p.map(word_autocorr, words)

      However, there's an issue with this because :meth:`word_acf` takes 3 arguments ``(word, text, timesteps)``.
      We could solve this using the :meth:`Pool.starmap` function:

      .. code-block:: python

         with Pool(4) as p:
             results = p.starmap(word_acf, [(i,j,k) for i,j,k in zip(words, 10*[text], 10*[timestep])]

      But this might be somewhat inefficient because ``10*[text]`` might take up quite a lot of memory.
      One workaround is to use the ``partial`` method from ``functools`` which returns a new function with 
      partial application of the given arguments:

      .. code-block:: python

         from functools import partial
         word_acf_partial = partial(word_autocorr, text=text, timesteps=timesteps)
         with Pool(4) as p:
             results = p.map(word_acf_partial, words)

   .. solution::

      .. literalinclude:: exercise/autocorrelation_multiproc.py
         :language: python
   

.. exercise:: Write an MPI version of word-autocorrelation

   Just like with ``multiprocessing``, the most natural MPI solution parallelizes over 
   the words used to compute the word-autocorrelation.  
   For educational purposes, both point-to-point and collective communication 
   implementations will be demonstrated here.

   Start by importing mpi4py (``from mpi4py import MPI``) at the top of the script.

   Here is a new function which takes care of managing MPI tasks.
   The problem needs to be split up between ``N`` ranks, and the method needs to be general 
   enough to handle cases where the number of words is not a multiple of the number of ranks.
   Below we see a standard algorithm to accomplish this. The function also calls 
   two functions which implement point-to-point and collective communication, respectively, to collect 
   individual results to one rank which computes the average

   .. literalinclude:: exercise/autocorrelation_mpi.py
      :pyobject: mpi_acf
      :emphasize-lines: 11-12, 14-16, 18-20


   .. discussion:: What type of communication can we use?

      The end result should be an average of all the word-autocorrelation functions. 
      What type of communication can be used to collect the results on one rank which 
      computes the average and prints it to file?

   Study the two "faded" MPI function implementations below, one using point-to-point communication and the other using 
   collective communication. Try to figure out what you should replace the ``____`` with.

   .. tabs:: 

      .. tab:: Point-to-point

         .. code-block:: python

            def ave_word_acf_p2p(comm, my_words, text, timesteps=100):
                rank = comm.Get_rank()
                n_ranks = comm.Get_size()
                # each rank computes its own set of acfs
                my_acfs = np.zeros((len(____), timesteps))
                for i, word in enumerate(my_words):
                    my_acfs[i,:] = word_acf(word, text, timesteps)

                if ____ == ____:
                    results = []
                    # append own results
                    results.append(my_acfs)
                    # receive data from other ranks and append to results
                    for sender in range(1, ____):
                        results.append(comm.____(source=sender, tag=12))
                    # compute total 
                    acf_tot = np.zeros((timesteps,))
                    for i in range(____):
                        for j in range(len(results[i])):
                            acf_tot += results[i][j]
                    return acf_tot
                else:
                    # send data
                    comm.____(my_acfs, dest=____, tag=12)

      .. tab:: Collective

         .. code-block:: python

               def ave_word_acf_gather(comm, my_words, text, timesteps=100):
                   rank = comm.Get_rank()
                   n_ranks = comm.Get_size() 
                   # each rank computes its own set of acfs
                   my_acfs = np.zeros((len(____), timesteps))
                   for i, word in enumerate(my_words):
                       my_acfs[i,:] = word_acf(word, text, timesteps)

                   # gather results on rank 0
                   results = comm.____(____, root=0)
                   # loop over ranks and results. result is a list of lists of ACFs
                   if ____ == ____:
                       acf_tot = np.zeros((timesteps,))
                       for i in range(n_ranks):
                           for j in range(len(results[i])):
                               acf_tot += results[i][j]
                       return acf_tot



   After implementing one or both of these functions, run your code and time the result for different number of tasks!

   .. code-block:: console

      $ time mpirun -np <N> python source/autocorrelation.py data/pg58.txt processed_data/pg58.dat results/pg58_acf.csv


   .. solution:: 

      .. literalinclude:: exercise/autocorrelation_mpi.py


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
