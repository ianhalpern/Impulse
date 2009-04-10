
def load_theme( screenlet ):
	pass

def on_draw( audio_sample_array, cr ):

	l = len( audio_sample_array )

	width, height = ( 544, 100 )

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
