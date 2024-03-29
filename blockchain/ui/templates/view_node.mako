<%inherit file="body.mako"/>
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
