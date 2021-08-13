<html lang="en">
    <%include file="header.mako"/>
    <body>
        <%include file="node_info.mako"/>
        <div>
            <table>
                <thead>
                    <tr>
                        <th>Network Nodes</th>
                        <th>Endpoints</th>
                    </tr>
                </thead>
                <tbody>
                    %for node in nodes:
                        <tr>
                            <td class="uuid">
                                %if node.resolved:
                                    ${node.id}
                                %else:
                                    unresponsive
                                %endif
                            </td>
                            <td>
                                <a href="${node.url}">${node.url}</a>
                            </td>
                        </tr>
                    %endfor
                </tbody>
            </table>
        </div>
        <div class="shortcut-links">
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
                    %for link in links:
                        <tr>
                            <td>${link['title']}</td>
                            <td><a href="${link['href']}">${link['href']}</a></td>
                        </tr>
                    %endfor
                </tbody>
            </table>
        </div>
    </body>
</html>
