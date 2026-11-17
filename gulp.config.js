/**
 * @file        gulp.config
 * @description Agnostic and modular Gulp configuration
 * @author      Selectra Front End Team
 * @version     1.0.6
 */

module.exports = {


  /**
   * @description Used to compile Sass to CSS
   * @memberof cfg
   * @property {object} sass
   */
  sass:
    {
      src:    './src/scss/widget.scss',
      dorMin: false,
      dev:
        {
          path:        './dev/css/',
          srcmaps:     true,
          srcmapsPath: './map',
        },
      prod:
        {
          path:        './dist/css/',
          srcmaps:     false,
          srcmapsPath: './map',
        },
      test:
        {
          path:        './testing/css/',
          srcmaps:     true,
          srcmapsPath: './map',
        },
    },


  /**
   * @description Used to purge css file from unused css rules
   * @memberof cfg
   * @property {object} purgecss
   */
  purgecss:
    {
      prod:
        {
          content:                   [ './dist/**/*.html', './dist/js/**/*.js' ],
          dest:                      [ './dist/css/' ],
          src:                       [ './dist/css/*.css' ],
          whitelist:                 [],
          whitelistChildren:         [],
          whitelistPatterns:         [ /^tippy/ ],
          whitelistPatternsChildren: [ /^tippy/ ],
        }
    },


  /**
   * @description Used to convert rem to px units.
   * @memberof cfg
   * @property {object} remtopx
   */
  remtopx:
    {
      dev:  './dev/css/',
      prod: './dist/css/',
      test: './testing/css/',
    },


  /**
   * @description Used to replace -- by - in classes for MEP (layout classes).
   * @memberof cfg
   * @property {object} mep
   */
  mep:
    {
      classes:
        [
          [ 'badge--', 'badge-' ],
          [ 'btn--', 'btn-' ],
          [ 'btn-help--', 'btn-help-' ],
          [ 'icon--', 'icon-' ],
          [ 'u-anim--', 'u-anim-' ],
          [ 'u-display--', 'u-display-' ],
          [ 'u-img--', 'u-img-' ],
          [ 'youtube-embed--', 'youtube-embed-' ],
        ],
      dev:
        {
          css:
            {
              dest: [ './dev/css/' ],
              src:  [ './dev/css/**/*.css' ],
            },
          js:
            {
              dest: [ './dev/js/' ],
              src:  [ './dev/js/**/*.js' ],
            }
        },
      prod:
        {
          css:
            {
              dest: [ './dist/css/' ],
              src:  [ './dist/css/**/*.css' ],
            },
          js:
            {
              dest: [ './dist/js/' ],
              src:  [ './dist/js/**/*.js' ],
            }
        }
    },


  /**
   * @description Used to generate critical css
   * @memberof cfg
   * @property {object} critical
   */
  critical:
    {
      dev:  './dev/',
      prod: './dist/',
      test: './testing/'
    },


  /**
   * @description Used to compile ES2015+/ES6+ to ES5
   * @memberof cfg
   * @property {object} script
   */
  script:
    {
      src:    [ './src/js/widget-launcher.js' ],
      dorMin: false,
      dev:
        {
          path:        './dev/js/',
          srcmaps:     true,
          srcmapsPath: './map',
        },
      prod:
        {
          path:        './dist/js/',
          srcmaps:     false,
          srcmapsPath: './map',
        },
      test:
        {
          path:        './testing/js/',
          srcmaps:     true,
          srcmapsPath: './map',
        }
    },


  /**
   * @description Used to minify and copy polyfills.
   * @memberof cfg
   * @property {object} polyfill
   */
  polyfill:
    {
      src: './node_modules/integration-common-files/src/js/00-polyfills/*.js',
      dev:  { path: './dev/js/polyfill/' },
      prod: { path: './dist/js/polyfill/' },
      test: { path: './testing/js/polyfill/' }
    },


  /**
   * @description Used to compile PUG to HTML
   * @memberof cfg
   * @property {object} pug
   */
  pug:
    {
      basedir: './',
      src:     './test-page/pug/05-pages/*.pug',
      dev:
        {
          path:       './dev/',
          indentSize: 2,
        },
      prod:
        {
          path:       './dist/',
          indentSize: 2,
        },
      test:
        {
          path:       './testing/',
          indentSize: 2,
        }
    },


  /**
   * @description Used to start BrowserSync
   * @memberof cfg
   * @property {object} bsync
   */
  bsync:
    {
      dev:
        {
          baseDir:   './dev/',
          directory: true,
          https:     false,
          http2:     false,
        },
      prod:
        {
          baseDir:   './dist/',
          directory: true,
          https:     false,
          http2:     false
        },
      test:
        {
          baseDir:   './testing/',
          directory: true,
          https:     false,
          http2:     false,
        },
    },


  /**
   * @description Used to clean files
   * @memberof cfg
   * @property {object} clean
   */
  clean: {
    dev:
      {
        all:  [ './dev/*' ],
        css:  [ './dev/css/' ],
        data: [ './dev/js/data/' ],
        font: [ './dev/font/' ],
        html: [ './dev/**/*.html' ],
        img:  [ './dev/img/' ],
        js:   [ './dev/js/' ],
      },
    prod:
      {
        all:  [ './dist/*' ],
        css:  [ './dist/css/' ],
        data: [ './dist/js/data/' ],
        font: [ './dist/font/' ],
        html: [ './dist/**/*.html' ],
        img:  [ './dist/img/' ],
        js:   [ './dist/js/' ],
      },
    test:
      {
        all:  [ './testing/*' ],
        css:  [ './testing/css/' ],
        data: [ './testing/js/data/' ],
        font: [ './testing/font/' ],
        html: [ './testing/**/*.html' ],
        img:  [ './testing/img/' ],
        js:   [ './testing/js/' ],
      }
  },


  /**
   * @description Used to copy static files
   * @memberof cfg
   * @property {object} copy
   */
  copy:
    {
      src: {
        data: [ './src/js/data/*' ],
        font: [ './src/font/*' ],
        img:
          [
            './src/img/**/*',
            '!src/img/**/src/',
            '!src/img/**/src/**/*',
            '!src/img/**/old/',
            '!src/img/**/old/**/*',
          ]
      },
      dev:
        {
          data: [ './dev/js/data/' ],
          font: [ './dev/font/' ],
          img:  [ './dev/img/' ],
        },
      prod:
        {
          data: [ './dist/js/data/' ],
          font: [ './dist/font/' ],
          img:  [ './dist/img/' ],
        },
      test:
        {
          data: [ './testing/js/data/' ],
          font: [ './testing/font/' ],
          img:  [ './testing/img/' ],
        }
    },


  /**
   * @description Used to watch files
   * @memberof cfg
   * @property {object} watch
   */
  watch:
    {
      src:
        {
          pug:    [ './src/pug/**/*.pug' ],
          sass:   [ './src/scss/**/*.scss' ],
          script: [ './src/js/**/*.js' ],
        }
    },

};
