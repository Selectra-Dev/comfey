import appLoader from 'integration-common-files/src/js/00-utilities/app-loader';
import widget from './widget';

/**
 * @file        widget-launcher
 * @description widget-launcher description
 * @author      Selectra Front End Team
 * @requires    './widget.js'
 * @requires    'integration-common-files/src/js/00-utilities/app-loader.js'
 */

/**
 * @memberof window
 * @property {object} drupalSettings
 * @property {string} drupalSettings.themePath
 *     Base path for the parent drupal theme.
 * @property {string} drupalSettings.activeThemePath
 *     Base path for the active drupal sub-theme.
 */

const

  drupalBasePath =
    ( function getBasePath() {
      const hasThemePath =
        window.drupalSettings &&
        typeof window.drupalSettings.themePath === 'string';
      return hasThemePath ? window.drupalSettings.themePath : null;
    }()),

  drupalActivePath =
    ( function getActivePath() {
      const hasActivePath =
        window.drupalSettings &&
        typeof window.drupalSettings.activeThemePath === 'string';
      return hasActivePath ? window.drupalSettings.activeThemePath : null;
    }()),

  appPaths =
    {

      // Application Configuration / Data file.
      data: ( function evalDataPath() {
        let basePath = '';
        if ( drupalActivePath ) {
          basePath = `/${ drupalActivePath }`;
        } else if ( drupalBasePath ) {
          basePath = `/${ drupalBasePath }`;
        }
        return `${ basePath }/js/data/widget-data.json`;
      }()),

      // Full polyfill bundle path.
      polyfillsFull: (
        drupalBasePath ?
          `/${ drupalBasePath }/js/polyfill/polyfill-full.min.js` :
          '/js/polyfill/polyfill-full.min.js'
      ),

      // Partial polyfill bundle path.
      polyfillsPartial: (
        drupalBasePath ?
          `/${ drupalBasePath }/js/polyfill/polyfill-partial.min.js` :
          '/js/polyfill/polyfill-partial.min.js'
      ),

      // Application styles.
      appCss: (
        drupalBasePath ?
          `/${ drupalBasePath }/css/widget.css` :
          '/css/widget.css'
      )
    };


appLoader({
  appCode: widget,
  appArgs: [ appPaths.data ],
  executeOn: 'load',
  polyfillUrls:
    {
      full:    appPaths.polyfillsFull,
      partial: appPaths.polyfillsPartial
    },
  // injections: []
});
