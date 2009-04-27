from screenlets.options import ColorOption, IntOption

fft = True

peak_heights = [ 0 for i in range( 256 ) ]
peak_acceleration = [ 0.0 for i in range( 256 ) ]

bar_color = ( 0.0, 0.6, 1.0, 0.8 )
peak_color = ( 1.0, 0.0, 0.0, 0.8 )

n_cols = 10
col_width = 16
col_spacing = 1

n_rows = 30
row_height = 3
row_spacing = 1

def load_theme ( screenlet ):

	screenlet.resize( n_cols * col_width + n_cols * col_spacing, 100 )

	screenlet.add_option( ColorOption(
		'Impulse', 'bar_color',
		bar_color, 'Bar color',
		'Example options group using color'
	) )

	screenlet.add_option( ColorOption(
		'Impulse', 'peak_color',
		peak_color, 'Peak color',
		'Example options group using color')
	)

	screenlet.add_option( IntOption(
		'Impulse', 'n_cols',
		n_cols, 'Number of columns',
		'Example options group using integer',
		min=1, max=256
	) )

	screenlet.add_option( IntOption(
		'Impulse', 'col_width',
		col_width, 'Column width',
		'Example options group using integer',
		min=1, max=256
	) )

	screenlet.add_option( IntOption(
		'Impulse', 'col_spacing',
		col_spacing, 'Column Spacing',
		'Example options group using integer',
		min=1, max=256
	) )

	screenlet.add_option( IntOption(
		'Impulse', 'n_rows',
		n_rows, 'Number of rows',
		'Example options group using integer',
		min=1, max=256
	) )

	screenlet.add_option( IntOption(
		'Impulse', 'row_height',
		row_height, 'Row height',
		'Example options group using integer',
		min=1, max=256
	) )

	screenlet.add_option( IntOption(
		'Impulse', 'row_spacing',
		row_spacing, 'Row Spacing',
		'Example options group using integer',
		min=1, max=256
	) )

def on_after_set_attribute ( self, name, value, screenlet ):
	setattr( self, name, value )
	screenlet.resize( n_cols * ( col_width + col_spacing ), n_rows * ( row_height + row_spacing ) )

def on_draw ( audio_sample_array, cr, screenlet ):

	freq = len( audio_sample_array ) / n_cols

	for i in range( 0, len( audio_sample_array ), freq ):

		col = i / freq
		rows = int( audio_sample_array[ i ] * n_rows )

		cr.set_source_rgba( bar_color[ 0 ], bar_color[ 1 ], bar_color[ 2 ], bar_color[ 3 ] )

		if rows > peak_heights[ i ]:
			peak_heights[ i ] = rows
			peak_acceleration[ i ] = 0.0
		else:
			peak_acceleration[ i ] += .1
			peak_heights[ i ] -= peak_acceleration[ i ]

		if peak_heights[ i ] < 0:
			peak_heights[ i ] = 0

		for row in range( 0, rows ):

			cr.rectangle(
				col * ( col_width + col_spacing ),
				screenlet.height - row * ( row_height + row_spacing ),
				col_width, -row_height
			)

		cr.fill( )

		cr.set_source_rgba( peak_color[ 0 ], peak_color[ 1 ], peak_color[ 2 ], peak_color[ 3 ] )

		cr.rectangle(
			col * ( col_width + col_spacing ),
			screenlet.height - peak_heights[ i ] * ( row_height + row_spacing ),
			col_width, -row_height
		)

		cr.fill( )

	cr.fill( )
	cr.stroke( )

