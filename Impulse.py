#!/usr/bin/env python
#
#+   Copyright (c) 2009 Ian Halpern
#@   http://Spectrolet.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, gtk, cairo, time, random, struct, signal, gobject
from gtk import gdk

#from numpy import *

from cimpulse import cimpulse

if gtk.pygtk_version < ( 2, 9, 0 ):
	print "PyGtk 2.9.0 or later required"
	raise SystemExit

pixmap = None

peak_heights = [ 0 for i in range( 32 ) ]

# This is called when we need to draw the windows contents
def expose ( widget, event=None ):
	global pixmap

	widget.window.draw_drawable( widget.window.new_gc( ), pixmap,
        # Only copy the area that was exposed.
        event.area.x, event.area.y,
        event.area.x, event.area.y,
        event.area.width, event.area.height )
	return True


def draw ( ):
	global pixmap

	fft = True

	audio_sample_array = cimpulse.getSnapshot( fft )

	if fft:
		ffted_array = audio_sample_array

		l = len( ffted_array ) / 4

		width, height = pixmap.get_size( )

		cst = cairo.ImageSurface( cairo.FORMAT_ARGB32, width, height )

		cr = cairo.Context( cst )

		# start drawing spectrum

		n_bars = 32
		bar_width = 16
		bar_spacing = 1

		for i in range( 1, l, l / n_bars ):

			cr.set_source_rgba( 0.0, 0.6, 1.0, 0.8 )
			#bar_amp_norm = audio_sample_array[ i ]

			bar_amp_norm = ffted_array[ i ]

			bar_height = bar_amp_norm * height + 3

			peak_index = int( ( i - 1 ) / ( l / n_bars ) )
			#print peak_index

			if bar_height > peak_heights[ peak_index ]:
				peak_heights[ peak_index ] = bar_height
			else:
				peak_heights[ peak_index ] -= 3

			if peak_heights[ peak_index ] < 3:
				peak_heights[ peak_index ] = 3

			for j in range( 0, int( bar_height / 3 ) ):
				cr.rectangle(
					( bar_width + bar_spacing ) * ( i / ( l / n_bars ) ),
					height - j * 3,
					bar_width,
					-2
				)

			cr.fill( )

			cr.set_source_rgba( 1.0, 0.0, 0.0, 0.8 )
			cr.rectangle(
				( bar_width + bar_spacing ) * ( i / ( l / n_bars ) ),
				height - int( peak_heights[ peak_index ] ),
				bar_width,
				-2
			)

			cr.fill( )

		cr.fill( )
		cr.stroke( )
	else:

		l = len( audio_sample_array )

		width, height = pixmap.get_size( )

		cst = cairo.ImageSurface( cairo.FORMAT_ARGB32, width, height )

		cr = cairo.Context( cst )

		# start drawing spectrum

		cr.set_source_rgba( 0.0, 0.6, 1.0, 0.8 )

		n_bars = 32
		bar_width = 16
		bar_spacing = 1

		for i in range( 0, l, l / n_bars ):

			bar_amp_norm = audio_sample_array[ i ]

			bar_height = bar_amp_norm * height + 2

			cr.rectangle(
				( bar_width + bar_spacing ) * ( i / ( l / n_bars ) ),
				height / 2 - bar_height / 2,
				bar_width,
				bar_height
			)

		cr.fill( )
		cr.stroke( )


	# end drawing

	cr_pixmap = pixmap.cairo_create( )

	cr_pixmap.set_source_rgba( 1.0, 1.0, 1.0, 0.0 ) # Transparent
	# Draw the background
	cr_pixmap.set_operator( cairo.OPERATOR_SOURCE )
	cr_pixmap.paint( )

	cr_pixmap.set_source_surface( cst, 0, 0 )
	cr_pixmap.paint( )

	return False

def screenChanged ( widget, old_screen=None ):

	# To check if the display supports alpha channels, get the colormap
	screen = widget.get_screen( )
	colormap = screen.get_rgba_colormap( )
	# Now we have a colormap appropriate for the screen, use it
	widget.set_colormap( colormap )

	return False

def timerExecFrame ( win ):
	global pixmap

	draw( )

	width, height = pixmap.get_size( )
	win.queue_draw_area( 0, 0, width, height )
	win.window.process_updates( True )

	return True


#def triggerRedraw ( win ):
#	width, height = win.get_size( )
#	win.queue_draw_area(0, 0, width, height)
#	win.window.process_updates( True )


def main(args):
	global pixmap

	width = 544
	height = 100

	screen = gdk.screen_get_default( )

	win = gtk.Window( )

	win.set_title( 'Spectrumize' )
	win.set_default_size( width, height )

	win.stick( )
	win.set_keep_below( True )
	win.set_decorated( False )
	win.set_skip_taskbar_hint( True )
	#win.set_gravity( gdk.GRAVITY_CENTER )

	win.connect( 'delete-event', gtk.main_quit )
	win.connect( 'expose-event', expose )
	win.connect( 'screen-changed', screenChanged )

	# initialize for the current display
	screenChanged( win )
	# Run the program
	win.show_all( )

	pixmap = gdk.Pixmap( win.window, width, height, -1 )

	# Tell GTK+ that we want to draw the windows background ourself.
	win.set_app_paintable(  True )
	win.set_double_buffered( False )

	screen_rect = screen.get_monitor_geometry( 0 )

	win.move( screen_rect.width / 2 - width / 2 + screen_rect.x, screen_rect.height / 2 - height / 2 + screen_rect.y  )


	gobject.timeout_add( 33, timerExecFrame, win )

	try:
		gtk.main( )
	except KeyboardInterrupt:
		pass

	print total_peak_heights

	return True

if __name__ == '__main__':

	try:
		import ctypes
		libc = ctypes.CDLL('libc.so.6')
		libc.prctl(15, os.path.split( sys.argv[ 0 ] )[ 1 ], 0, 0, 0)
	except:
		pass

	#signal.signal( signal.SIGINT, discontinueProcessing )
	sys.exit( main( sys.argv ) )

