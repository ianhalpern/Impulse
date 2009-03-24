/*
 *
 * pa_operation* pa_context_get_source_info_by_index(pa_context *c, uint32_t id, pa_source_info_cb_t cb, void *userdata);
 * pa_operation_unref(pa_context_get_source_info_list(c, get_source_info_callback, NULL));
 * static void get_source_info_callback(pa_context *c, const pa_source_info *i, int is_last, void *userdata) {
 * 	i->index,
 * 	i->name,
 * 	i->driver,
 * 	i->description

	static char *device = NULL;
	pa_xfree(device);
	device = pa_xstrdup(optarg);

 pa_stream_set_read_callback(stream, stream_read_callback, NULL);
 */

#include <Python.h>

#include <string.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>

#include <pulse/pulseaudio.h>

#define CHUNK 1024

uint8_t filler[ CHUNK ], snapshot[ CHUNK ];
int filler_index = 0;

static pa_context *context = NULL;
static pa_stream *stream = NULL;

static pa_io_event* stdio_event = NULL;
static pa_mainloop_api *mainloop_api = NULL;
static char *stream_name = NULL, *client_name = NULL, *device = NULL;
static void *buffer = NULL;
static size_t buffer_length = 0, buffer_index = 0;

//static int actions = 1;

static pa_sample_spec sample_spec = {
	.format = PA_SAMPLE_S16LE,
	.rate = 44100,
	.channels = 2
};

static pa_stream_flags_t flags = 0;

static pa_channel_map channel_map;
static int channel_map_set = 0;

/* A shortcut for terminating the application */
static void quit(int ret) {
    assert(mainloop_api);
    mainloop_api->quit(mainloop_api, ret);
}

/* UNIX signal to quit recieved */
static void exit_signal_callback(pa_mainloop_api*m, pa_signal_event *e, int sig, void *userdata) {
    quit(0);
}

/*static void context_drain_complete(pa_context *c, void *userdata) {
    pa_context_disconnect(c);
}

static void drain(void) {
    pa_operation *o;
    if (!(o = pa_context_drain(context, context_drain_complete, NULL)))
        pa_context_disconnect(context);
    else
        pa_operation_unref(o);
}


static void complete_action(void) {
    assert(actions > 0);

    if (!(--actions))
        drain();
}*/

static void get_source_info_callback(pa_context *c, const pa_source_info *i, int is_last, void *userdata) {
	if (is_last) {
		//complete_action();
		return;
	}

	assert(i);

	//printf( "%s\n", i->name );
	//fflush(stdout);
	device = pa_xstrdup( i->name );

	if (( pa_stream_connect_record(stream, device, NULL, flags)) < 0) {
		fprintf(stderr, "pa_stream_connect_record() failed: %s\n", pa_strerror(pa_context_errno(c)));
		quit(1);
	}
}

/* This is called whenever new data may is available */
static void stream_read_callback(pa_stream *s, size_t length, void *userdata) {

    const void *data;
    assert(s);
    assert(length > 0);

    if (stdio_event)
        mainloop_api->io_enable(stdio_event, PA_IO_EVENT_OUTPUT);

    if (pa_stream_peek(s, &data, &length) < 0) {
        fprintf(stderr, "pa_stream_peek() failed: %s\n", pa_strerror(pa_context_errno(context)));
        quit(1);
        return;
    }

    assert(data);
    assert(length > 0);

    if (buffer) {
        fprintf(stderr, "Buffer overrun, dropping incoming data\n");
        if (pa_stream_drop(s) < 0) {
            fprintf(stderr, "pa_stream_drop() failed: %s\n", pa_strerror(pa_context_errno(context)));
            quit(1);
        }
        return;
    }

    buffer = pa_xmalloc(buffer_length = length);
    memcpy(buffer, data, length);
    buffer_index = 0;
    pa_stream_drop(s);
}

/* Some data may be written to STDOUT */
static void stdout_callback(pa_mainloop_api*a, pa_io_event *e, int fd, pa_io_event_flags_t f, void *userdata) {
    ssize_t r;

    assert(a == mainloop_api);
    assert(e);
    assert(stdio_event == e);

    if (!buffer) {
        mainloop_api->io_enable(stdio_event, PA_IO_EVENT_NULL);
        return;
    }

    assert(buffer_length);

	int excess = filler_index + buffer_length - ( CHUNK );

	if ( excess < 0 ) excess = 0;

	memcpy( filler + filler_index, buffer, buffer_length - excess );
	filler_index += buffer_length - excess;

	//if ( strlen( filler ) != filler_index)
	//	fprintf( stderr, "ERROR!\n" );

	if ( excess ) {
		memcpy( snapshot, filler, filler_index );
		//fprintf( stderr, "%d\n", filler_index);
		//filler[ 0 ] = 0;
		filler_index = 0;
	}


    //snapshot = pa_xmalloc(buffer_length);
	//memcpy( snapshot, buffer, buffer_length );
    /*if ((r = write(fd, (uint8_t*) buffer+buffer_index, buffer_length)) <= 0) {
        fprintf(stderr, "write() failed: %s\n", strerror(errno));
        quit(1);

        mainloop_api->io_free(stdio_event);
        stdio_event = NULL;
        return;
    }*/
	r = buffer_length;
    buffer_length -= r;
    buffer_index += r;

    if (!buffer_length) {
        pa_xfree(buffer);
        buffer = NULL;
        buffer_length = buffer_index = 0;
    }
}

static void context_state_callback(pa_context *c, void *userdata) {

	switch (pa_context_get_state(c)) {
		case PA_CONTEXT_CONNECTING:
		case PA_CONTEXT_AUTHORIZING:
		case PA_CONTEXT_SETTING_NAME:
			break;
		case PA_CONTEXT_READY:
			assert(c);
			assert(!stream);

			if (!(stream = pa_stream_new(c, stream_name, &sample_spec, channel_map_set ? &channel_map : NULL))) {
				fprintf(stderr, "pa_stream_new() failed: %s\n", pa_strerror(pa_context_errno(c)));
				quit(1);
			}

			pa_stream_set_read_callback(stream, stream_read_callback, NULL);

			pa_operation_unref( pa_context_get_source_info_by_index( c, 0, get_source_info_callback, NULL ) );

			break;
		case PA_CONTEXT_TERMINATED:
			quit(0);
			break;

		case PA_CONTEXT_FAILED:
		default:
			fprintf(stderr, "Connection failure: %s\n", pa_strerror(pa_context_errno(c)));
			quit(1);
	}
}

void *pa_threadStart( void *ptr ) {
	int ret = 1;
	pa_mainloop* pa_m;
	pa_m = (pa_mainloop*) ptr;
	if (pa_mainloop_run(pa_m, &ret) < 0) {
		fprintf(stderr, "pa_mainloop_run() failed.\n");
	//	goto quit;
	}
	return (void *) NULL;
}

static PyObject * cimpulse_system( PyObject *self, PyObject *args ) {
	const char *command;
	int sts;

	if ( ! PyArg_ParseTuple( args, "s", &command ) )
		return NULL;
	sts = system( command );
	return Py_BuildValue( "i", sts );
}

static PyObject * cimpulse_getMonitorDevice( PyObject *self, PyObject *args ) {
	return PyString_FromString( device );
	//return PyString_FromString( "hi" );
}

static PyObject * cimpulse_getSnapshot( PyObject *self, PyObject *args ) {
	return PyString_FromStringAndSize( snapshot, CHUNK );
	//return PyString_FromString( "hi" );
}

static PyObject *CimpulseError;

static PyMethodDef CimpulseMethods[ ] = {
	{ "system",  cimpulse_system, METH_VARARGS, "Execute a shell command." },
	{ "getMonitorDevice",  cimpulse_getMonitorDevice, METH_VARARGS, "Execute a shell command." },
	{ "getSnapshot",  cimpulse_getSnapshot, METH_VARARGS, "Execute a shell command." },
	{ NULL, NULL, 0, NULL }        /* Sentinel */
};

PyMODINIT_FUNC initcimpulse ( void ) {
	PyObject *m;

	m = Py_InitModule( "cimpulse", CimpulseMethods );
	if (m == NULL)
		return;

	CimpulseError = PyErr_NewException( "cimpulse.error", NULL, NULL );
	Py_INCREF( CimpulseError );
	PyModule_AddObject( m, "error", CimpulseError );

	// Pulseaudio
	int r;
	char *server = NULL;
	pa_mainloop* pa_m = NULL;

	client_name = pa_xstrdup( "cimpulse" );
	stream_name = pa_xstrdup( "cimpulse" );

	// Set up a new main loop

	if ( ! ( pa_m = pa_mainloop_new( ) ) ) {
		fprintf( stderr, "pa_mainloop_new() failed.\n" );
	}

	mainloop_api = pa_mainloop_get_api( pa_m );

	r = pa_signal_init(mainloop_api);
	assert(r == 0);
    //pa_signal_new(SIGINT, exit_signal_callback, NULL);
    //pa_signal_new(SIGTERM, exit_signal_callback, NULL);

    if (!(stdio_event = mainloop_api->io_new(mainloop_api,
                                             STDOUT_FILENO,
                                             PA_IO_EVENT_OUTPUT,
                                             stdout_callback, NULL))) {
        fprintf(stderr, "io_new() failed.\n");
        goto quit;
    }
	// create a new connection context
	if (!(context = pa_context_new(mainloop_api, client_name))) {
		fprintf(stderr, "pa_context_new() failed.\n");
		goto quit;
	}

	pa_context_set_state_callback( context, context_state_callback, NULL);

	/* Connect the context */
	pa_context_connect(context, server, 0, NULL);


	// pulseaudio thread
	pthread_t thread1;
	int iret;

	iret = pthread_create( &thread1, NULL, pa_threadStart, (void*) pa_m);

	/* Run the main loop */
	/*if (pa_mainloop_run(pa_m, &ret) < 0) {
		fprintf(stderr, "pa_mainloop_run() failed.\n");
		goto quit;
	}*/
	return;
quit:
	if ( context )
		pa_context_unref( context );
	if ( pa_m ) {
		pa_signal_done( );
		pa_mainloop_free( pa_m );
	}
	pa_xfree( buffer );
	pa_xfree( device );
	pa_xfree( client_name );
}

