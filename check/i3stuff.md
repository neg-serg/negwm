@on(CommandEvent("container-info"))
@static(last_id=0)
async def container_info(i3, event):
    """Show information about the focused container."""
    tree = await i3.get_tree()
    window = tree.find_focused()
    if not window:
        return
    logger.info(f"window raw information: {window.ipc_data}")
    summary = "About focused container"
    r = window.rect
    w = window
    info = {
        "name": w.name,
        "title": w.window_title,
        "class": w.window_class,
        "instance": w.window_instance,
        "role": w.window_role,
        "type": w.ipc_data["window_type"],
        "sticky": w.sticky,
        "floating": w.floating,
        "geometry": f"{r.width}×{r.height}+{r.x}+{r.y}",
        "layout": w.layout,
        "parcent": w.percent,
        "marks": ", ".join(w.marks) or "(none)",
    }
    body = "\n".join(
        (
            f"<tt>{k:10}</tt> {html.escape(str(v))}"
            for k, v in info.items()
            if v is not None
        )
    )
    result = await notify(
        i3,
        app_icon="info",
        expire_timeout=10000,
        summary=summary,
        body=body,
        replaces_id=container_info.last_id,
    )
    container_info.last_id = result[0]


@on(CommandEvent("workspace-info"))
@static(last_id=0)
async def workspace_info(i3, event):
    """Show information about the focused workspace."""
    workspaces = await i3.get_workspaces()
    focused = [w for w in workspaces if w.focused]
    if not focused:
        return
    workspace = focused[0]
    summary = f"Workspace {workspace.num} on {workspace.output}"
    tree = await i3.get_tree()
    workspace = [w for w in tree.workspaces() if w.num == workspace.num]

    def format(container):
        if container.focused:
            style = 'foreground="#ffaf00"'
        elif not container.window:
            style = 'foreground="#6c98ee"'
        else:
            style = ""
        if container.window:
            content = (
                f"{(container.window_class or '???').lower()}: "
                f"{(container.window_title or '???')}"
            )
        elif container.type == "workspace" and not container.nodes:
            # Empty workspaces use workspace_layout, but when default,
            # this is layout...
            layout = container.ipc_data["workspace_layout"]
            if layout == "default":
                layout = container.layout
            content = f"({layout})"
        else:
            content = f"({container.layout})"
        root = f"<span {style}>{content.lower()}</span>"
        children = []
        for child in container.nodes:
            if child == container.nodes[-1]:
                first = "└─"
                others = "  "
            else:
                first = "├─"
                others = "│ "
            content = format(child).replace("\n", f"\n<tt>{others}</tt>")
            children.append(f"<tt>{first}</tt>{content}")
        children.insert(0, root)
        return "\n".join(children)

    body = format(workspace[0]).lstrip("\n")
    result = await notify(
        i3,
        app_icon="system-search",
        expire_timeout=20000,
        summary=summary,
        body=body,
        replaces_id=workspace_info.last_id,
    )
    workspace_info.last_id = result[0]
