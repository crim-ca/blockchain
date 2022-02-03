<div class="body-menu">
    <div class="node-info">
        <table>
            <thead>
                <tr>
                    <th>Current Node</th>
                    <th>Endpoint</th>
                    <th colspan="${len(ui_shortcuts)}">Shortcuts</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="uuid">${node_id}</td>
                    <td><a href="${node_url}">${node_url}</a></td>
                    %for link in ui_shortcuts:
                        <td><a href="${link['href']}">${link['title']}</a></td>
                    %endfor
                </tr>
            </tbody>
        </table>
    </div>
</div>
