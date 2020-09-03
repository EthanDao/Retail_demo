odoo.define('list.editable.customize', function (require) {
    "use strict";
    var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
    var fieldRegistry = require('web.field_registry');
    var ListRenderer = require('web.ListRenderer');
    var core = require('web.core');
    var ListCustomizeWidth = ListRenderer.extend({
        /**
         * We want section and note to take the whole line (except handle and trash)
         * to look better and to hide the unnecessary fields.
         *
         * @override
         */
        init: function (parent, state, params) {
            this._super.apply(this, arguments);
        },
        // Over ride
        _freezeColumnWidths: function () {
            //fix title width is 150px
            // todo sh@dowalker
            if (!this.columnWidths && this.el.offsetParent === null) {
                // there is no record nor widths to restore or the list is not visible
                // -> don't force column's widths w.r.t. their label
                return;
            }
            const thElements = [...this.el.querySelectorAll('table thead th')];
            if (!thElements.length) {
                return;
            }
            const table = this.el.getElementsByTagName('table')[0];
            let columnWidths = this.columnWidths;

            if (!columnWidths || !columnWidths.length) { // no column widths to restore
                // Set table layout auto and remove inline style to make sure that css
                // rules apply (e.g. fixed width of record selector)
                table.style.tableLayout = 'auto';
                thElements.forEach(th => {
                    th.style.width = null;
                    th.style.maxWidth = null;
                });

                // Resets the default widths computation now that the table is visible.
                // call function core, ignore syntax( ok van goi core bth)
                this._computeDefaultWidths();

                // Squeeze the table by applying a max-width on largest columns to
                // ensure that it doesn't overflow
                columnWidths = this._squeezeTable();
            }

            thElements.forEach((th, index) => {
                // Width already set by default relative width computation
                if (th.dataset['name'] == 'name') {
                    th.style.maxWidth = '200px';
                    th.style.width = '200px';
                }
                else if (th.dataset['name'] == 'code'){
                    th.style.maxWidth = '85px';
                    th.style.width = '85px';
                }
                    else if (th.dataset['name'] == 'note') {
                    th.style.maxWidth = '150px';
                    th.style.width = '150px';
                }
                else if (th.dataset['name'] == 'row' || th.dataset['name'] == 'col'){
                    th.style.maxWidth = '85px';
                    th.style.width = '85px';
                }
                else {
                    if (!th.style.width) {
                        th.style.width = `${columnWidths[index]}px`;
                    }
                }
            });

            // Set the table layout to fixed
            table.style.tableLayout = 'fixed';
        },
    });

    var X_ListCustomizeWidth = FieldOne2Many.extend({
        /**
         * We want to use our custom renderer for the list.
         *
         * @override
         */
        _getRenderer: function () {
            if (this.view.arch.tag === 'tree') {
                return ListCustomizeWidth;
            }
            return this._super.apply(this, arguments);
        },
    });

    fieldRegistry.add('x_list_customize_width', X_ListCustomizeWidth);

    return ListCustomizeWidth;
});