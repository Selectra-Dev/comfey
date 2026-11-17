/**
 * @file        widget
 * @description widget description
 * @author      Selectra Front End Team
 */

/**
 * @memberof window
 * @property {object} selectraWidgets
 * @property {Function} selectraWidgets.widgetLogInfo
 */


/**
 * @typedef {object} appData
 * @description Application data.
 *
 * @property {*} property
 */


const appInfo = {
  name:    'widget',
  version: '0.0.0',
};


/**
 * @function widget
 * @description widget description
 * @param {string} dataPath
 *     Path to the widget json configuration/data file.
 */
export default function widget( dataPath ) {

  /**
   * @function widgetLogic
   * @param {appData} init
   *     Configuration/data object.
   */
  function widgetLogic( init ) {
    // Build the widget functionality here.
    console.log( init );
  }

  /**
   * @function doManageErrors
   * @description Manage errors.
   * @param {object} error
   *     Error object.
   */
  function doManageErrors( error ) {
    // Suggestion:
    // Try to manage errors and...
    // executeWidget();
    // ** Be aware of infinite loops! **
    console.log( error );
  }


  /**
   * @function doFinally
   * @description doFinally description
   */
  function doFinally() {
    // Finally code.
  }

  // Helper functions
  window.selectraWidgets =
    {
      ...window.selectraWidgets,
      widgetLogInfo: () => {
        console.info( `${ appInfo.name } ${ appInfo.version }` );
      }
    };

  // Fetch data & execute
  ( function executeWidget() {
    const fetchInit =
      {
        method: 'GET',
        mode:   'cors',
      };
    fetch( dataPath, fetchInit )
      .then(
        response => {
          if ( 200 === response.status ) {
            return response.json;
          } else {
            throw {
              error: 'fetch() error',
              resource: dataPath,
              status: response.status
            };
          }
        }
      ).then(
        widgetLogic
      ).catch(
        doManageErrors
      ).finally(
        doFinally
      );

    // For widgets with no data requirements...
    // try {
    //   widgetLogic();
    // } catch ( error ) {
    //   doManageErrors( error );
    // } finally {
    //   doFinally();
    // }

  }());

}
