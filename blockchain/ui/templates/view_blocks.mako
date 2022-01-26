<%inherit file="body.mako"/>
<%include file="node_info.mako"/>
<%include file="chain_info.mako"/>
<% import json %>
<div>
    <table class="block-list">
        <thead>
            <tr>
                <th colspan="5">
                    Blocks Metadata in Blockchain
                </th>
            </tr>
            <tr>
                <th>Index</th>
                <th>UUID</th>
                <th>Created</th>
                <th>Previous Hash</th>
                <th>Content Changes</th>
            </tr>
        </thead>
        <tbody>
            %for block in blocks:
            <tr>
                <td>${block["index"]}</td>
                <td class="uuid">${block["id"]}</td>
                <td>${block["created"]}</td>
                <td class="hash">${block.get("previous_hash")}
                    %if block["index"] == 0:
                        (<i>genesis block</i>)
                    %endif
                </td>
                <td>
                    <details>
                        <summary>Expand to view Consents</summary>
                        <!-- no newlines because they will appear -->
                        <pre><code class="language-json">${json.dumps(block["consents"], indent=2)}</code></pre>
                    </details>
                </td>
            </tr>
            %endfor
        </tbody>
    </table>
</div>
