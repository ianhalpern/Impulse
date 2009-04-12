fft = True

peak_heights = [ 0 for i in range( 32 ) ]
peak_acceleration = [ 0.0 for i in range( 32 ) ]

def load_theme ( screenlet ):
	screenlet.resize( 170, 100 )

def on_draw ( audio_sample_array, cr ):

		ffted_array = audio_sample_array

		l = len( ffted_array ) / 4

		width, height = ( 170, 100 )

		# start drawing spectrum

		n_bars = 10
		bar_width = 16
		bar_spacing = 1

		for i in range( 1, l, l / n_bars ):

			cr.set_source_rgba( 0.0, 0.6, 1.0, 0.8 )
			#bar_amp_norm = audio_sample_array[ i ]

			bar_amp_norm = ffted_array[ i ]

			bar_height = bar_amp_norm * ( height - 6 ) + 3

			peak_index = int( ( i - 1 ) / ( l / n_bars ) )
			#print peak_index

			if bar_height > peak_heights[ peak_index ]:
				peak_acceleration[ peak_index ] = 0.0
				peak_heights[ peak_index ] = bar_height
			else:
				peak_acceleration[ peak_index ] += .3
				peak_heights[ peak_index ] -= peak_acceleration[ peak_index ]

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

