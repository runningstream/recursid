# R3cuR$1d

## Description
This is a framework for reading data from sources, processing it to produce more data, then outputting it somewhere to sinks.

It is designed to handle any kind of data, with "input modules" reading data from sources like log files, JSON files, or 0MQ Fluentd output.  Input modules can produce any type of object they want, and it can be specific to the source like a "Fluentd Log Line" or generic, like "Text Line".

Each object produced by an input module gets fed to every "reemitter module" and "output module" at the same time.  Each output module can handle one or multiple types of object, and can output that object in any way needed.  For instance, output modules can output "Log Lines" to the screen, or send them to a Logstash input socket.  Output modules can save a "Downloaded File" to disk, or to Amazon S3.

Reemitter modules take the objects they're fed and do something with the data in them, then they can send output objects back to the beginning to be processed or output more.  They don't reemit the same objects they took in - those objects were already processed by every reemitter and output module - they just output new objects describing new data.

A reemitter module might take a Log Line or a Downloaded File, look for any URLs embedded in it, then output a "URL" object.  A separate reemitter module might take URL objects, download them with multiple user-agents, then reemit Downloaded File objects for other modules to parse.

An output module might take Downloaded Files and record information in a database about their URL and the hash of the downloaded data.

This type of flexible system makes recursive handling of data producing other data simple, but can lead to infinite loops.  That's why objects produced by input modules get a "time-to-live" value, and any time a reemitter module produces a new object based on that input object, the new object gets a "time-to-live" one less than the original.  Output modules do not produce any inputs, only reemitter modules can produce this looping behavior.

## Building
Run `./build_dist.sh`, the package is in `dist` now.

## Installing
To install Recursid and have it execute at startup, run:

```bash
sudo pip3 install dist/Recursid-0.1.0-py3-none-any.whl
sudo cp /usr/local/lib/python3.*/site-packages/recursid/etc/systemd/system/recursid.service /etc/systemd/system
```

Now modify `/etc/systemd/system/recursid.service` to reflect the config.json file you want recursid to use, or copy your config into `/usr/local/etc/recursid/recursid.json`.  Examples are in `/usr/local/lib/python3.*/site-packages/recursid/etc/recursid`.  You can place your config file anywhere nobody/nogroup will be able to read, as that is who Recursid will run as.

You can test your configuration file via `/usr/local/bin/recursid_multithread.py` or `/usr/local/bin/recursid_multiprocess.py`, specifying the desired configuration file as argument.

Now running the commands below will cause recursid to execute at startup.

```bash
sudo systemctl enable recursid
sudo service recursid restart
```

If you're using the sqlite3 output module, as some of the sample configurations use, you'll have to create the directory where sqlite3 must put the database.  Make sure you make it read/write/execute for nobody/nogroup, so Recursid can write there.
