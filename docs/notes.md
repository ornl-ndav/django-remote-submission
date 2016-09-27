# Notes

These are some notes from trying to get this project set up.

## Installing Pycrypto gives an error about `gmp.h`

I was having troubles installing Pycrypto on my Mac. It was complaining about
`gmp.h`, even though I had gmp installed. This is the error I got:

```console
$ make depend
source venv/bin/activate && \
	python -m pip install -r requirements.txt && \
	touch .depend.secondary

...

  clang -Wno-unused-result -Wsign-compare -Wunreachable-code -fno-common -dynamic -fwrapv -Wall -Wstrict-prototypes -isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk -I/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk/System/Library/Frameworks/Tk.framework/Versions/8.5/Headers -std=c99 -O3 -fomit-frame-pointer -Isrc/ -I/usr/include/ -I/usr/local/Cellar/python3/3.5.1/Frameworks/Python.framework/Versions/3.5/include/python3.5m -c src/_fastmath.c -o build/temp.macosx-10.10-x86_64-3.5/src/_fastmath.o
  src/_fastmath.c:36:11: fatal error: 'gmp.h' file not found
  # include <gmp.h>
            ^
  1 error generated.
  error: command 'clang' failed with exit status 1

  ----------------------------------------
  Failed building wheel for pycrypto

...
```

The solution is to modify the `CFLAGS` environment variable, which pip is using
to compile that C file that the error occurred in. Here's the command I ended up
using:

```console
$ CFLAGS='-I/usr/local/include -L/usr/local/lib' make depend
```

Alternatively, it would have worked with

```console
$ env CFLAGS='-I/usr/local/include -L/usr/local/lib' make depend
```

Either is fine.

[Source](http://stackoverflow.com/questions/15375171/pycrypto-install-fatal-error-gmp-h-file-not-found)

## Setting up a VM for testing fabric

I wanted to set up a VM so that I can test out fabric without using an external
server (plus, I'll need a VM later to test out other applications). One of the
challenges was being able to SSH into the server. Here's what I ended up needing
to do (with VirtualBox):

1. Go to VirtualBox's preferences > Network > Host-only Networks

2. Add a new network with whatever name you want

3. Create a new machine for the CentOS disk (I named mine CentOS7)

4. Under CentOS7 > Settings > Network > Adapter 1, set it to Bridged Adapter.

5. Under CentOS7 > Settings > Network > Adapter 2, enable it and set it to a
   Host-only Adapter using the adapter we made earlier.

6. Run the VM, load the CentOS ISO, and install

7. In the VM, `ip addr show` and find the right IP address

8. On the host, `ssh <USER>@<IP ADDR>`

## Designing the application for running code remotely

We want to be able to execute code remotely. Initially, I was thinking that we
could use Fabric to manage some of the complexity inherent with that. One of the
biggest with this idea is that Fabric isn't threadsafe.

In order to run a job on the remote server, we have a couple of options:

1. Create a server that runs on the cluster, waiting for new jobs to execute,
   and then executing them. This could either be a period polling mechanism
   (every 5 minutes, check for a new script) or a push-based system (when I
   receive a request to run something, then I'll run it immediately).

2. Create an additional server on the web server machine, which functions the
   same as the other one, but has multiple processes running which can use
   Fabric or some similar library to remotely connect to the cluster, start the
   job, and wait for its completion.

3. Connect to the cluster inside the Django code, spawning a new thread for each
   job that needs to be submitted, starting the job on the cluster, waiting for
   its completion, and saving the results in the database.

\#1 isn't the best choice for a Django application/library like this one,
because it requires extra code to be running on the remote server. It's possible
to do that, but I think one of the other choices would be better.

\#2 could work, but it also introduces a lot of complexity because now, instead
of just running 1 server, you're running 2 or more servers, each of which have
the be maintained and could run run into their own problems that need to be
debugged separately.

\#3 is the best solution, I think. The benefit here is that all of the code for
the application stays in the application. One downside is that we would not be
able to use Fabric's API to connect to the other hosts, because Fabric is
inherently not thread-safe. Instead, we would have to use a lower level library,
like Paramiko (which Fabric is built on).
