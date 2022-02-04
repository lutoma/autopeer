const gulp         = require('gulp'),
	sass         = require('gulp-sass')(require('sass'));
	autoprefixer = require('gulp-autoprefixer')
	strip        = require('gulp-strip-css-comments')
	del          = require('del')

// Compile SCSS files to CSS
gulp.task('scss', () => {
	del(['static/css/screen.css'])
	return gulp.src(['scss/screen.scss'])
	.pipe(sass({
		outputStyle : 'compressed',
		includePaths: 'node_modules'
	}))
	.pipe(autoprefixer())
	.pipe(strip({preserve: false}))
	.pipe(gulp.dest('static/css'))
})

gulp.task('fonts', () => {
	return gulp.src([
		'node_modules/@fortawesome/fontawesome-pro/webfonts/*',
		'node_modules/typeface-fira-sans/files/*'
	])
	.pipe(gulp.dest('static/fonts'))
})

gulp.task('js-libs', () => {
	return gulp.src([
		'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js',
		'node_modules/bootstrap/dist/js/bootstrap.bundle.min.js.map',
	])
	.pipe(gulp.dest('static/js'))
})

// Watch asset folder for changes
gulp.task('watch', gulp.series('scss', 'js-libs', 'fonts', () => {
	gulp.watch('scss/**/*', gulp.series('scss'))
}))

gulp.task('build', gulp.series('scss', 'js-libs', 'fonts'))
gulp.task('default', gulp.series('watch'))
