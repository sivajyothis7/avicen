frappe.views.Workspace = class CustomWorkspace extends frappe.views.Workspace {
    setup_actions(page) {
        let pages = page.public ? this.public_pages : this.private_pages;
        let current_page = pages.filter((p) => p.title == page.name)[0];

        if (!this.is_read_only) {
            this.setup_customization_buttons(current_page);
            return;
        }

        this.clear_page_actions();

        if (frappe.user.has_role("System Manager")) {
            this.page.set_secondary_action(
                __("Edit"),
                async () => {
                    if (!this.editor || !this.editor.readOnly) return;
                    this.is_read_only = false;
                    this.toggle_hidden_workspaces(true);
                    await this.editor.readOnly.toggle();
                    this.editor.isReady.then(() => {
                        this.body.addClass("edit-mode");
                        this.initialize_editorjs_undo();
                        this.setup_customization_buttons(current_page);
                        this.show_sidebar_actions();
                        this.make_blocks_sortable();
                    });
                },
                "es-line-edit"
            );

            this.page.add_inner_button(__("Create Workspace"), () => {
                this.initialize_new_page();
            });
        }
    }
};
