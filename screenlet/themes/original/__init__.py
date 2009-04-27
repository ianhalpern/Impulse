from screenlets.options import ColorOption, IntOption

co = ( 0.0, 0.6, 1.0, 0.8 )

def load_theme( screenlet ):
	screenlet.resize( 544, 100 )

	screenlet.add_option( ColorOption(
		'Impulse', 'co',
		co, 'Color',
		'Example options group using color'
	) )

def on_after_set_attribute ( self, name, value, screenlet ):
	setattr( self, name, value )

def on_draw( audio_sample_array, cr, screenlet ):

	l = len( audio_sample_array )

	width, height = ( 544, 100 )

	# start drawing spectrum

	cr.set_source_rgba( co[ 0 ], co[ 1 ], co[ 2 ], co[ 3 ] )

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
