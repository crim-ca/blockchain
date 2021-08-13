<div class="chain-info">
    <table>
        <thead>
        <tr>
            <th>Current Blockchain</th>
            <th>Number of Blocks</th>
            <th colspan="${len(shortcuts)}">
                Shortcuts
            </th>
        </tr>
        </thead>
        <tbody>
        <tr>
            <td class="uuid">${chain}</td>
            <td>${count}</td>
            %for chain_link in shortcuts:
                <td><a href="${chain_link["href"]}">${chain_link["title"]}</a></td>
            %endfor
        </tr>
        </tbody>
    </table>
</div>
