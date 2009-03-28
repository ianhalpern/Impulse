/*
 *
 */

#include <Python.h>

#include <string.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include <pulse/pulseaudio.h>

#include <fftw3.h>
#include <math.h>

#define CHUNK 1024

int16_t buffer[ CHUNK / 2 ], snapshot[ CHUNK / 2 ];
static size_t buffer_index = 0;

static pa_context *context = NULL;
static pa_stream *stream = NULL;
static pa_threaded_mainloop* mainloop = NULL;
static pa_io_event* stdio_event = NULL;
static pa_mainloop_api *mainloop_api = NULL;
static char *stream_name = NULL, *client_name = NULL, *device = NULL;


static pa_sample_spec sample_spec = {
	.format = PA_SAMPLE_S16LE,
	.rate = 44100,
	.channels = 2
};

static pa_stream_flags_t flags = 0;

static pa_channel_map channel_map;
static int channel_map_set = 0;

/* A shortcut for terminating the application */
static void quit( int ret ) {
	assert( mainloop_api );
	mainloop_api->quit( mainloop_api, ret );
}

static void get_source_info_callback( pa_context *c, const pa_source_info *i, int is_last, void *userdata ) {
	if ( is_last )
		return;

	assert(i);

	device = pa_xstrdup( i->name );

	if ( ( pa_stream_connect_record( stream, device, NULL, flags ) ) < 0 ) {
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

	int excess = buffer_index * 2 + length - ( CHUNK );

	if ( excess < 0 ) excess = 0;

	memcpy( buffer + buffer_index, data, length - excess );
	buffer_index += ( length - excess ) / 2;

	if ( excess ) {
		memcpy( snapshot, buffer, buffer_index * 2 );
		buffer_index = 0;
	}

	pa_stream_drop(s);
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

static void stop_pa (void) {

	pa_threaded_mainloop_stop( mainloop );

	printf( "exit\n" );
}

static PyObject * cimpulse_getMonitorDevice( PyObject *self, PyObject *args ) {
	return PyString_FromString( device );
}

static PyObject * cimpulse_getSnapshot( PyObject *self, PyObject *args ) {
	PyObject *magnitude;

	int fft = 1;

	if ( ! fft ) {
		magnitude = PyTuple_New( CHUNK / 2 );
		int i;
		for ( i = 0; i < CHUNK / 2; i++ ) {
			PyObject *x;
			x = PyLong_FromLong(snapshot[ i ]);
			PyTuple_SetItem( magnitude, i, x );
		}
	} else {
		magnitude = PyTuple_New( CHUNK / 4 );

		double *in;
		fftw_complex *out;
		fftw_plan p;

		in = (double*) malloc( sizeof( double ) * ( CHUNK / 2 ) );
		out = (fftw_complex*) fftw_malloc( sizeof( fftw_complex ) * ( CHUNK / 2 ) );

		if ( snapshot != NULL ) {
			int i;
			for ( i = 0; i < CHUNK / 2; i++ ) {
				in[ i ] = (double) snapshot[ i ];
			}
		}

		p = fftw_plan_dft_r2c_1d( CHUNK / 2, in, out, 0 );

		fftw_execute( p );

		fftw_destroy_plan( p );

		if ( out != NULL ) {
			int i;
			for ( i = 0; i < CHUNK / 4; i++ ) {
				PyObject *x;
				x = PyLong_FromDouble( sqrt( pow( out[ i ][ 0 ], 2 ) + pow( out[ i ][ 1 ], 2 ) ) );
				PyTuple_SetItem( magnitude, i, x );
			}
		}

		//Py_DECREF( magnitude );

		free( in );
		fftw_free(out);
	}

	return magnitude; // PyString_FromStringAndSize( (char *) snapshot, CHUNK );
}

static PyObject *CimpulseError;

static PyMethodDef CimpulseMethods[ ] = {
	{ "getMonitorDevice",  cimpulse_getMonitorDevice, METH_VARARGS, "Returns the name of the Pulseaudio source device Cimpulse is recording." },
	{ "getSnapshot",  cimpulse_getSnapshot, METH_VARARGS, "Returns the current audio snapshot from Pulseaudio." },
	{ NULL, NULL, 0, NULL }		/* Sentinel */
};

PyMODINIT_FUNC initcimpulse ( void ) {
	PyObject *m;

	m = Py_InitModule( "cimpulse", CimpulseMethods );
	if (m == NULL)
		return;

	CimpulseError = PyErr_NewException( "cimpulse.error", NULL, NULL );
	Py_INCREF( CimpulseError );
	PyModule_AddObject( m, "error", CimpulseError );

	Py_AtExit( &stop_pa );

	// Pulseaudio
	int r;
	char *server = NULL;

	client_name = pa_xstrdup( "cimpulse" );
	stream_name = pa_xstrdup( "cimpulse" );

	// Set up a new main loop

	if ( ! ( mainloop = pa_threaded_mainloop_new( ) ) ) {
		fprintf( stderr, "pa_mainloop_new() failed.\n" );
		return;
	}

	mainloop_api = pa_threaded_mainloop_get_api( mainloop );

	r = pa_signal_init( mainloop_api );
	assert( r == 0 );

	/*if (!(stdio_event = mainloop_api->io_new(mainloop_api,
											 STDOUT_FILENO,
											 PA_IO_EVENT_OUTPUT,
											 stdout_callback, NULL))) {
		fprintf(stderr, "io_new() failed.\n");
		goto quit;
	}*/

	// create a new connection context
	if ( ! ( context = pa_context_new( mainloop_api, client_name ) ) ) {
		fprintf( stderr, "pa_context_new() failed.\n" );
		return;
	}

	pa_context_set_state_callback( context, context_state_callback, NULL );

	/* Connect the context */
	pa_context_connect( context, server, 0, NULL );

	// pulseaudio thread
	pa_threaded_mainloop_start( mainloop );

	return;
}

