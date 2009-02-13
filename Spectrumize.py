#!/usr/bin/env python

import os, sys, gtk, cairo, time, random, struct, signal
from gtk import gdk
from threading import Thread

if gtk.pygtk_version < ( 2, 9, 0 ):
	print "PyGtk 2.9.0 or later required"
	raise SystemExit

CHUNK = 1024    # audio stream buffer size

supports_alpha = False
keep_processing = True

sample = ""

# This is called when we need to draw the windows contents
def expose ( widget, event=None ):
	global supports_alpha, sample

	#print "expose"

	if not sample:
		sample = ""

		#for x in range( CHUNK ):
		#	sample += chr( int( random.random( ) * 256 ) )

	sample = sample.ljust( CHUNK, chr( 0x00 ) )


	cr = widget.window.cairo_create( )

	if supports_alpha == True:
		cr.set_source_rgba( 1.0, 1.0, 1.0, 0.0 ) # Transparent
	else:
		cr.set_source_rgb( 1.0, 1.0, 1.0 ) # Opaque white

	# Draw the background
	cr.set_operator( cairo.OPERATOR_SOURCE )
	cr.paint( )

	# Draw a circle
	(width, height) = widget.get_size( )
	cr.set_source_rgba( 0.0, 0.6, 1.0, 0.9 )

	for i in range( 0, CHUNK, CHUNK / 32 ):
		bar_freq = struct.unpack( 'i', sample[ i:i+4 ] )[ 0 ]

		#normalize
		bar_freq_norm = bar_freq / float( 0xffffff7f )

		bar_freq_norm *= 2 # magnify

		bar_heigth = bar_freq_norm * height + 2

		bar_width = 16
		bar_spacing = 1

		cr.rectangle(
			( bar_width + bar_spacing ) * ( i / ( CHUNK / 32 ) ),
			height / 2 - bar_heigth / 2,
			bar_width,
			bar_heigth
		)

	cr.arc( 0, 0, 1, 0, 2.0 * 3.14 )

	cr.fill( )
	cr.stroke( )

	#print struct.unpack( '4i', sample[:16] )
	return False

def screen_changed ( widget, old_screen=None ):

	global supports_alpha

	# To check if the display supports alpha channels, get the colormap
	screen = widget.get_screen( )
	colormap = screen.get_rgba_colormap( )
	if colormap == None:
		colormap = screen.get_rgb_colormap( )
		supports_alpha = False
	else:
		supports_alpha = True

	# Now we have a colormap appropriate for the screen, use it
	widget.set_colormap( colormap )

	return False

def discontinue_processing(signl, frme):
    global keep_processing
    keep_processing = False
    return 0

def captureAudio ( win ):
	global keep_processing, sample

	audio_stream = os.popen3( "esdmon" )

	triggerRedraw( win )
	while keep_processing:
		sample = audio_stream[ 1 ].read( CHUNK )
		#win.window.redraw_canvas( )
		triggerRedraw( win )
		#expose( win, sample )

	for stream in audio_stream:
		stream.close( )

	print "\nHelper Thread Die..."

def triggerRedraw ( win ):
	width, height = win.get_size( )
	win.queue_draw_area(0, 0, width, height)
	win.window.process_updates( True )

def main(args):
	global keep_processing



	win = gtk.Window( )

	win.set_title( 'Spectrumize' )
	win.set_default_size( 544, 300 )

	win.connect( 'delete-event', gtk.main_quit )

	# Tell GTK+ that we want to draw the windows background ourself.
	# If we don't do this then GTK+ will clear the window to the
	# opaque theme default color, which isn't what we want.
	win.set_app_paintable(  True )
	#win.unset_flags( gtk.DOUBLE_BUFFERED )
	win.connect( 'expose-event', expose )
	win.connect( 'screen-changed', screen_changed )

	win.set_decorated( False )
	win.set_skip_taskbar_hint( True )

	# toggle title bar on click - we add the mask to tell 
	# X we are interested in this event
	win.add_events( gdk.BUTTON_PRESS_MASK )

	# initialize for the current display
	screen_changed( win )

	# Run the program
	win.show_all( )

	t = Thread( target=captureAudio, args=(win,) )
	t.start( )

	try:
		while keep_processing:
			time.sleep( 1 )
	except KeyboardInterrupt:
		print "Error: KeyboardInterrupt Caught..."
		discontinue_processing( )

	t.join( )

	print "Main Thead Die..."
	return True

if __name__ == '__main__':
	signal.signal( signal.SIGINT, discontinue_processing )
	sys.exit( main( sys.argv ) )

