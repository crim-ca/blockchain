<html lang="en">
    <%include file="header.mako"/>
    <body>
        <div class="chains">
            %if chains:
            <table class="chain-list">
                <thead>
                    <tr>
                        <th rowspan="2">Chain</th>
                        <th colspan="${len(chains[0]["shortcuts"])}">
                            Shortcuts
                        </th>
                        <th colspan="${len(chains[0]["links"])}">
                            API Links
                        </th>
                    </tr>
                    <tr>
                        %for link_type in ["shortcuts", "links"]:
                            %for chain_link in chains[0][link_type]:
                                <th>${chain_link["title"]}</th>
                            %endfor
                        %endfor
                    </tr>
                </thead>
                <tbody>
                    %for chain_info in chains:
                    <tr>
                        <td>${chain_info["id"]}</td>
                        %for link_type in ["shortcuts", "links"]:
                            %for chain_link in chain_info[link_type]:
                                <td>
                                    <a href="${chain_link['href']}">${chain_link['title']}</a>
                                </td>
                            %endfor
                        %endfor
                    </tr>
                    %endfor
                </tbody>
            </table>
            %else:
                <div class="warning">No available chains!</div>
            %endif
        </div>
    </body>
</html>
