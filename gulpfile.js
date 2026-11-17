/**
 * @file Gulpfile build from tasks folder.
 * @author Selectra Front End Team <florian.leblois@selectra.info>
 * @version 1.0.7
 */

const
  env = process.env.NODE_ENV || 'dev',
  toolsPath = './node_modules/design-system-tools/gulp/',
  { parallel, series } = require( 'gulp' ),
  { assets, clean, copy, sprite } = require( `${ toolsPath }tasks/assets` ),
  { css, compileCss, criticalCss, purgeCss, remToPx } = require( `${ toolsPath }tasks/css` ),
  { html } = require( `${ toolsPath }tasks/html` ),
  { mep, mepCss, mepScript } = require( `${ toolsPath }tasks/mep` ),
  { polyfill, script } = require( `${ toolsPath }tasks/script` ),
  { server } = require( `${ toolsPath }tasks/server` ),
  { watchAll, watchAllMep } = require( `${ toolsPath }tasks/watch` ),
  { getTask } = require( `${ toolsPath }tools/dynamic-task` ),

  /**
   * Define tasks for dynamic one
   */
  compilecss = compileCss,
  criticalcss = criticalCss,
  mepcss = mepCss,
  mepscript = mepScript,
  purgecss = purgeCss,
  remtopx = remToPx;

/**
 * Dynamic tasks
 */
let
  build = null,
  watch = null;
switch ( getTask()) {
case 'base':
  build = series( clean, parallel( assets, html, series( script, polyfill )), css );
  watch = watchAll;
  break;
case 'mep':
  build = env === 'prod' ?
    series( clean, parallel( assets, html, compilecss, series( script, polyfill )), mep, remtopx, purgecss ) :
    series( clean, parallel( assets, html, compilecss, script ), polyfill, mep, remtopx );
  watch = watchAllMep;
  break;
case 'appcfg':
  build = series( clean, parallel( assets, html, series( script, polyfill )), css, remtopx );
  watch = watchAll;
  break;
}

/**
 * Define latest tasks.
 */
// eslint-disable-next-line one-var
const
  work = parallel( server, watch ),
  start = series( build, work );

/**
 * Export tasks.
 */
module.exports = {
  assets,
  build,
  clean,
  copy,
  compilecss,
  css,
  criticalcss,
  html,
  mepcss,
  mepscript,
  polyfill,
  purgecss,
  remtopx,
  server,
  script,
  sprite,
  start,
  watch,
  work,
  default: start
};
