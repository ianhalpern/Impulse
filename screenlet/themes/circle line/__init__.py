import math

from screenlets.options import ColorOption, IntOption

fft=True

co = ( 0.0, 0.6, 1.0, 0.8 )

def load_theme( screenlet ):
	screenlet.resize( 300, 300 )

	screenlet.add_option( ColorOption(
		'Impulse', 'co',
		co, 'Color',
		'Example options group using color'
	) )

def on_after_set_attribute ( self, name, value, screenlet ):
	setattr( self, name, value )

def on_draw( audio_sample_array, cr, screenlet ):

	l = len( audio_sample_array )

	width, height = ( 300, 300 )

	cr.set_source_rgba( co[ 0 ], co[ 1 ], co[ 2 ], co[ 3 ] )

	n_bars = 32

	cr.set_line_width( 2 )

	h = 50

	fx = 0
	fy = 0

	for i in range( 0, l, l / n_bars ):

		bar_amp_norm = audio_sample_array[ i ]

		bar_height = bar_amp_norm * 100


		a = ( math.pi*2 / n_bars ) * ( i / ( l / n_bars ) )

		x = math.sin( a ) * ( h + bar_height ) + width / 2
		y = math.cos( a ) * ( h + bar_height ) + height / 2

		if not i:
			fx = x
			fy = y
			cr.move_to( x, y )

		cr.curve_to(
			x, y,
			x, y,
			x, y
		)

	cr.curve_to(
		fx, fy,
		fx, fy,
		fx, fy
	)

	cr.stroke( )
