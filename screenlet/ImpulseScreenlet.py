#!/usr/bin/env python
#
#+   Copyright (c) 2009 Ian Halpern
#@   http://impulse.ian-halpern.com
#
#    This file is part of Impulse.
#
#    Impulse is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Impulse is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Impulse.  If not, see <http://www.gnu.org/licenses/>.


import screenlets, sys, gobject, os
import cimpulse

class ImpulseScreenlet ( screenlets.Screenlet) :
	"""A PulseAudio graphical spectrum analyzer."""

	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'ImpulseScreenlet'
	__version__	= '0.1'
	__author__	= 'Ian Halpern'
	__desc__	= __doc__	# set description to docstring of class

	theme_module = None

	def __init__ ( self, **keyword_args ):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=200, height=200,
			uses_theme=True, **keyword_args)


		os.chdir( self.get_screenlet_dir( ) )
		sys.path.append( "themes" )

		# set theme
		self.theme_name = "default"

		self.timer = gobject.timeout_add( 33, self.update )


	def update (self):

		self.redraw_canvas()
		return True # keep running this event

	def on_init ( self ):
		self.add_default_menuitems( )

	def on_load_theme (self):
		"""Called when the theme is reloaded (after loading, before redraw)."""
		self.theme_module = __import__( self.theme_name )
		self.theme_module.load_theme( self )

	def resize ( self, w, h ):
		self.width = w
		self.height = h
		self.window.resize( w * self.scale, h * self.scale )

	def on_draw ( self, cr ):
		"""In here we draw"""

		cr.scale( self.scale, self.scale )

		if not self.theme_module: return

		fft = False

		if hasattr( self.theme_module, "fft" ) and self.theme_module.fft:
			fft = True

		audio_sample_array = cimpulse.getSnapshot( fft )

		self.theme_module.on_draw( audio_sample_array, cr )


	def on_draw_shape ( self, ctx ):
		self.on_draw(ctx)

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show it
if __name__ == "__main__":

	try:
		import ctypes
		libc = ctypes.CDLL('libc.so.6')
		libc.prctl(15, os.path.split( sys.argv[ 0 ] )[ 1 ], 0, 0, 0)
	except Exception:
		pass

	# create new session
	import screenlets.session
	screenlets.session.create_session( ImpulseScreenlet )
