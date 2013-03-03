'use strict';

pandora.ui.preferencesDialog = function() {

    var tabs = [
            {id: 'account', title: 'Account', selected: true},
            {id: 'advanced', title: 'Advanced'}
        ],
        $tabPanel = Ox.TabPanel({
            content: function(id) {
                var $content = Ox.Element()
                    .css({overflowY: 'auto'})
                    .append(
                        $('<img>')
                            .attr({src: '/static/png/icon.png'})
                            .css({
                                position: 'absolute',
                                left: '16px',
                                top: '16px',
                                width: '64px',
                                height: '64px'
                            })
                    );
                if (id == 'account') {
                    $content.append(
                        Ox.Form({
                            items: [
                                Ox.Input({
                                    disabled: true,
                                    id: 'username',
                                    label: 'Username',
                                    labelWidth: 120,
                                    value: pandora.user.username,
                                    width: 320
                                }),
                                Ox.Input({
                                        autovalidate: /.+/,
                                        id: 'password',
                                        label: 'New Password',
                                        labelWidth: 120,
                                        type: 'password',
                                        validate: pandora.validateNewPassword,
                                        width: 320
                                    })
                                    .bindEvent({
                                        validate: function(data) {
                                            data.valid && pandora.api.editPreferences({password: data.value});
                                        }
                                    }),
                                Ox.Input({
                                        autovalidate: pandora.autovalidateEmail,
                                        id: 'email',
                                        label: 'E-Mail Address',
                                        labelWidth: 120,
                                        validate: pandora.validateNewEmail,
                                        value: pandora.user.email,
                                        width: 320
                                    })
                                    .bindEvent({
                                        validate: function(data) {
                                            if (data.valid && data.value != pandora.user.email) {
                                                pandora.user.email = data.value;
                                                pandora.api.editPreferences({email: data.value});
                                            }
                                        }
                                    }),
                                Ox.Input({
                                    disabled: true,
                                    id: 'level',
                                    label: 'Level',
                                    labelWidth: 120,
                                    value: Ox.toTitleCase(pandora.user.level),
                                    width: 320
                                }),
                                Ox.Checkbox({
                                        id: 'newsletter',
                                        label: 'Newsletter',
                                        labelWidth: 120,
                                        title: pandora.user.newsletter ? 'Subscribed' : 'Unsubscribed',
                                        value: pandora.user.newsletter,
                                        width: 320
                                    })
                                    .bindEvent({
                                        change: function(data) {
                                            pandora.user.newsletter = data.value;
                                            this.options({
                                                title: pandora.user.newsletter ? 'Subscribed' : 'Unsubscribed'
                                            });
                                            pandora.api.editPreferences({
                                                newsletter: pandora.user.newsletter 
                                            });
                                        }
                                    })
                                
                            ]
                        })
                        .css({position: 'absolute', left: '96px', top: '16px'})
                    );
                } else {
                    $content.append(
                        Ox.Button({
                            title: 'Reset UI Settings...',
                            width: 160
                        })
                        .bindEvent({
                            click: function() {
                                pandora.$ui.resetUIDialog = pandora.ui.resetUIDialog().open();
                            }
                        })
                        .css({position: 'absolute', left: '96px', top: '16px'})
                    );
                    $content.append(
                        Ox.Button({
                            title: 'Run Script on Load...',
                            width: 160
                        })
                        .bindEvent({
                            click: function() {
                                pandora.$ui.onloadDialog = pandora.ui.onloadDialog().open();
                            }
                        })
                        .css({position: 'absolute', left: '96px', top: '40px'})
                    );
                }
                return $content;
            },
            tabs: tabs
        }),
        $dialog = Ox.Dialog({
            buttons: [
                Ox.Button({
                    id: 'signout',
                    title: 'Sign Out...'
                }).bindEvent({
                    click: function() {
                        $dialog.close();
                        pandora.UI.set({page: 'signout'});
                    }
                }),
                {},
                Ox.Button({
                    id: 'done',
                    title: 'Done'
                }).bindEvent({
                    click: function() {
                        $dialog.close();
                    }
                })
            ],
            closeButton: true,
            content: $tabPanel,
            height: 192,
            minHeight: 192,
            minWidth: 432,
            title: 'Preferences',
            width: 432
        }),
        closeDialog = $dialog.close;

    $dialog.close = function() {
        closeDialog();
        pandora.UI.set({page: ''});
    };

    return $dialog;

};
