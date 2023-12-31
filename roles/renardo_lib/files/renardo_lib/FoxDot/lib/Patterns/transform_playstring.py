from treelib import Node, Tree

def parse_playstring_tree(string):
    """Parse rhythmic patterns enclosed in numbered square brackets """
    openpar_index_stack = [] # store indexes of parenthesis opening chars
    result_parse_tree = Tree(identifier="parse_tree")
    result_parse_tree.create_node(string, "playstring_root")
    current_node = None
    current_parent_node = "playstring_root"
    for i, c in enumerate(string):
        if c == '[':
            result_parse_tree.create_node(c, i, parent=current_parent_node)
            current_node = None
            current_parent_node = i
            openpar_index_stack.append(i)
            # add a branch to the tree here
        elif c == ']' and openpar_index_stack:
            openpar_index = openpar_index_stack.pop()
            content_start = openpar_index + 1
            content = string[content_start:i]
            if openpar_index > 0 and string[openpar_index-1] in ['1','2','3','4','5','6','7','8','9']:
                openpar_index -= 1 # put the index on the number preceding parenthesis
                base = int(string[openpar_index])
            else:
                base = 1
            result_parse_tree[current_parent_node].tag = string[openpar_index:i+1]
            # new parsing to count subdivisions for the current content
            third_stack = []
            subdiv_counter = 0
            for I,C in enumerate(content):
                if C == '[':
                    if not third_stack: # only count as subdivisions characters not inside parenthesis (depth 0 => empty stack)
                        if I > 0 and content[I-1] in ['1','2','3','4','5','6','7','8','9']:
                            subdiv_counter += int(content[I-1])
                        else:
                            subdiv_counter += 1
                    third_stack.append(I)
                elif C == ']' and third_stack:
                    third_stack.pop()
                elif not third_stack and C in ['1','2','3','4','5','6','7','8','9']:
                    if I+1 < len(content) and content[I+1] != '[':
                        subdiv_counter += 1
                elif not third_stack and C not in ['(',')','[',']','<','>','{','}',',']:
                    subdiv_counter += 1
            #
            result_parse_tree[current_parent_node].data = {
                    "openpar_index": openpar_index,
                    "closepar_index": i,
                    "content_start": content_start,
                    "depth": len(openpar_index_stack),
                    "content": content,
                    "base": base, # on how many beats to play the patterns
                    "subdiv": subdiv_counter, # how many time subdivisions in the pattern to play
                  }
            current_node = None
            current_parent_node = result_parse_tree[current_parent_node].predecessor("parse_tree")
        elif current_node is None:
            # avoid numbers just before square brackets as they are base indications not sample to play
            if c in ['1','2','3','4','5','6','7','8','9'] and len(string) > i+1 and string[i+1] == '[':
                continue
            result_parse_tree.create_node(c, i, parent=current_parent_node)
            current_node = i
            result_parse_tree[current_node].data = {
                    "content_start": i,
                    "depth": len(openpar_index_stack),
                    "content": c,
                    # "base": 1, # on how many beats to play the patterns
                    # "subdiv": 1, # how many time subdivisions in the pattern to play
                  }
        else:
            if c in ['1','2','3','4','5','6','7','8','9'] and len(string) > i+1 and string[i+1] == '[':
                continue
            result_parse_tree[current_node].tag += c
            result_parse_tree[current_node].data["content"] += c
            # result_parse_tree[current_node].data["base"] += 1
            # result_parse_tree[current_node].data["subdiv"] += 1
        result_parse_tree[result_parse_tree.root].data = {
            "content_start": 0,
            "depth": 0,
            "content": string,
            # "base": 1, # on how many beats to play the patterns
        }
    return result_parse_tree

def padding(beat_number, baselist):
    spacedsublist = [[e]+[' ']*(beat_number-1) for e in baselist]
    spacedlinear = [e for sublist in spacedsublist for e in sublist]
    return spacedlinear

def compute_padding_values_in_tree(parse_tree):
    """ Calculate padding to apply to each node in the parse tree"""
    # for each node in the tree ...
    for node in parse_tree.expand_tree(mode=Tree.DEPTH, key=lambda k: k.identifier):
        # ... padding is the node rhythmic "base" (~= new subdivision of rhythmic group denoted by the number before square bracket) ...
        if 'base' in parse_tree[node].data:
            parse_tree[node].data["padding"] = parse_tree[node].data["base"]
        else:
            parse_tree[node].data["padding"] = 1
        # ... times the rhythmic subdivision values (how many subdivision the rhythmic pattern has) of each sibling and his children recursively
        for sibling in parse_tree.siblings(node):
            for sibling_child in parse_tree.expand_tree(nid=sibling.identifier, mode=Tree.DEPTH, key=lambda k: k.identifier):
                if 'subdiv' in parse_tree[sibling_child].data:
                    parse_tree[node].data["padding"] *= parse_tree[sibling_child].data["subdiv"]

def build_padded_playstring_in_tree(parse_tree):
    """ build padded result for each node beginning from the deepest leaf to the root """
    for level in range(parse_tree.depth()+1):
        for node in parse_tree.expand_tree(mode=Tree.WIDTH, key=lambda k: k.identifier):
            if parse_tree.depth() + 1 - level == parse_tree.depth(node) + 1:
                if not parse_tree.children(node):
                    to_padd = parse_tree[node].tag
                else:
                    to_padd = []
                    for child in parse_tree.children(node):
                        to_padd.extend(child.data["padded_result"])
                parse_tree[node].data["padded_result"] = padding(parse_tree[node].data["padding"], to_padd)

def rebase(subdiv, spacedlinear):
    rebased = [ spacedlinear[i:i+subdiv] for i in range(0, len(spacedlinear), subdiv) ]
    return rebased

def linearize_as_string(rebased_list):
    return [ '[' + "".join(sublist) + ']' for sublist in rebased_list ]

def rebase_and_linearize(subdiv, padded_playstring_list):
    return linearize_as_string(rebase(subdiv, padded_playstring_list))

def compute_rebase_stack_from_tree(parse_tree):
    """Create list of rebase to apply based on sudiv values in the tree"""
    rebase_stack = []
    # for each node in the tree ...
    for node in parse_tree.expand_tree(mode=Tree.DEPTH, key=lambda k: k.identifier):
        # ... rebase for each subdiv value different from 1
        if 'subdiv' in parse_tree[node].data and parse_tree[node].data["subdiv"] > 1:
            rebase_stack.append(parse_tree[node].data["subdiv"])
    return rebase_stack

def apply_rebase_and_linearize(rebase_stack, padded_result):
    result = padded_result
    # print(rebase_stack)
    for subdiv in rebase_stack:
        # print("=====================================================\n")
        # print(result)
        result = rebase_and_linearize(subdiv, result)
    return "".join(result)

def transform_playstring(string):
    parse_tree = parse_playstring_tree(string)
    compute_padding_values_in_tree(parse_tree)
    build_padded_playstring_in_tree(parse_tree)
    # print(parse_tree["playstring_root"].data["padded_result"])
    result = apply_rebase_and_linearize(
            compute_rebase_stack_from_tree(parse_tree),
            parse_tree["playstring_root"].data["padded_result"]
        )
    # print(result)
    return result

tps = transform_playstring
