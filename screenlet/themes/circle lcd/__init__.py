import math

from screenlets.options import ColorOption, IntOption

fft = True

cc = ( 0.0, 0.6, 1.0, 0.8 )

def load_theme( screenlet ):
	screenlet.resize( 300, 300 )

	screenlet.add_option( ColorOption(
		'Impulse', 'cc',
		cc, 'Color',
		'Example options group using color'
	) )


def on_after_set_attribute ( self, name, value, screenlet ):
	setattr( self, name, value )

def on_draw( audio_sample_array, cr, screenlet ):

	l = len( audio_sample_array )

	width, height = ( 300, 300 )

	cr.set_source_rgba( cc[ 0 ],  cc[ 1 ],  cc[ 2 ],  cc[ 3 ] )

	n_bars = 32

	cr.set_line_width( 4 )

	for i in range( 0, l, l / n_bars ):

		bar_amp_norm = audio_sample_array[ i ]

		bar_height = bar_amp_norm * 130 + 5

		for j in range( 0, int( bar_height / 5 ) ):
			cr.arc(
				width / 2,
				height / 2,
				20 + j * 5,
				( math.pi*2 / n_bars ) * ( i / ( l / n_bars ) ),
				( math.pi*2 / n_bars ) * ( i / ( l / n_bars ) + 1 ) - .05
			)

			cr.stroke( )
