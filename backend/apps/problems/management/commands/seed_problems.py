from django.core.management.base import BaseCommand
from apps.problems.models import Problem, TestCase

SEED_PROBLEMS = [
    {
        "title": "Two Sum",
        "slug": "two-sum",
        "difficulty": "Easy",
        "topics": ["Array", "Hash Table"],
        "patterns": ["Hash Map"],
        "description": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.",
        "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "-10^9 <= target <= 10^9", "Only one valid answer exists."],
        "examples": [
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."},
            {"input": "nums = [3,2,4], target = 6", "output": "[1,2]", "explanation": "Because nums[1] + nums[2] == 6, we return [1, 2]."}
        ],
        "starter_code": {
            "python": "def twoSum(nums: list[int], target: int) -> list[int]:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Contains Duplicate",
        "slug": "contains-duplicate",
        "difficulty": "Easy",
        "topics": ["Array", "Hash Table"],
        "patterns": ["Hash Set"],
        "description": "Given an integer array `nums`, return `true` if any value appears at least twice in the array, and return `false` if every element is distinct.",
        "constraints": ["1 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
        "examples": [
            {"input": "nums = [1,2,3,1]", "output": "true", "explanation": "1 appears twice."},
            {"input": "nums = [1,2,3,4]", "output": "false", "explanation": "All elements are distinct."}
        ],
        "starter_code": {
            "python": "def containsDuplicate(nums: list[int]) -> bool:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Valid Anagram",
        "slug": "valid-anagram",
        "difficulty": "Easy",
        "topics": ["String", "Hash Table"],
        "patterns": ["Frequency Count"],
        "description": "Given two strings `s` and `t`, return `true` if `t` is an anagram of `s`, and `false` otherwise.\n\nAn Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.",
        "constraints": ["1 <= s.length, t.length <= 5 * 10^4", "s and t consist of lowercase English letters."],
        "examples": [
            {"input": "s = \"anagram\", t = \"nagaram\"", "output": "true", "explanation": "Both strings contain exact same character counts."},
            {"input": "s = \"rat\", t = \"car\"", "output": "false", "explanation": "Character frequencies do not match."}
        ],
        "starter_code": {
            "python": "def isAnagram(s: str, t: str) -> bool:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Product of Array Except Self",
        "slug": "product-of-array-except-self",
        "difficulty": "Medium",
        "topics": ["Array", "Prefix Sum"],
        "patterns": ["Prefix/Suffix Array"],
        "description": "Given an integer array `nums`, return an array `answer` such that `answer[i]` is equal to the product of all the elements of `nums` except `nums[i]`.\n\nThe product of any prefix or suffix of `nums` is guaranteed to fit in a 32-bit integer.\n\nYou must write an algorithm that runs in `O(n)` time and without using the division operation.",
        "constraints": ["2 <= nums.length <= 10^5", "-30 <= nums[i] <= 30"],
        "examples": [
            {"input": "nums = [1,2,3,4]", "output": "[24,12,8,6]", "explanation": "For index 0: 2*3*4=24; index 1: 1*3*4=12; etc."}
        ],
        "starter_code": {
            "python": "def productExceptSelf(nums: list[int]) -> list[int]:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Maximum Subarray",
        "slug": "maximum-subarray",
        "difficulty": "Medium",
        "topics": ["Array", "Dynamic Programming"],
        "patterns": ["Kadane's Algorithm"],
        "description": "Given an integer array `nums`, find the subarray with the largest sum, and return its sum.",
        "constraints": ["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
        "examples": [
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "explanation": "The subarray [4,-1,2,1] has the largest sum 6."}
        ],
        "starter_code": {
            "python": "def maxSubArray(nums: list[int]) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Best Time to Buy and Sell Stock",
        "slug": "best-time-to-buy-and-sell-stock",
        "difficulty": "Easy",
        "topics": ["Array", "Dynamic Programming"],
        "patterns": ["Sliding Window", "Greedy"],
        "description": "You are given an array `prices` where `prices[i]` is the price of a given stock on the `i`-th day.\n\nYou want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.\n\nReturn the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return `0`.",
        "constraints": ["1 <= prices.length <= 10^5", "0 <= prices[i] <= 10^4"],
        "examples": [
            {"input": "prices = [7,1,5,3,6,4]", "output": "5", "explanation": "Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5."}
        ],
        "starter_code": {
            "python": "def maxProfit(prices: list[int]) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Valid Palindrome",
        "slug": "valid-palindrome",
        "difficulty": "Easy",
        "topics": ["Two Pointers", "String"],
        "patterns": ["Two Pointers"],
        "description": "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.\n\nGiven a string `s`, return `true` if it is a palindrome, or `false` otherwise.",
        "constraints": ["1 <= s.length <= 2 * 10^5", "s consists only of printable ASCII characters."],
        "examples": [
            {"input": "s = \"A man, a plan, a canal: Panama\"", "output": "true", "explanation": "\"amanaplanacanalpanama\" is a palindrome."}
        ],
        "starter_code": {
            "python": "def isPalindrome(s: str) -> bool:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Two Sum II - Input Array Is Sorted",
        "slug": "two-sum-ii",
        "difficulty": "Medium",
        "topics": ["Array", "Two Pointers", "Binary Search"],
        "patterns": ["Two Pointers"],
        "description": "Given a 1-indexed array of integers `numbers` that is already sorted in non-decreasing order, find two numbers such that they add up to a specific `target` number.",
        "constraints": ["2 <= numbers.length <= 3 * 10^4", "-1000 <= numbers[i] <= 1000", "numbers is sorted in non-decreasing order."],
        "examples": [
            {"input": "numbers = [2,7,11,15], target = 9", "output": "[1,2]", "explanation": "The sum of 2 and 7 is 9. Therefore index1 = 1, index2 = 2."}
        ],
        "starter_code": {
            "python": "def twoSum(numbers: list[int], target: int) -> list[int]:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "3Sum",
        "slug": "3sum",
        "difficulty": "Medium",
        "topics": ["Array", "Two Pointers", "Sorting"],
        "patterns": ["Sorting + Two Pointers"],
        "description": "Given an integer array nums, return all the triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.\n\nNotice that the solution set must not contain duplicate triplets.",
        "constraints": ["3 <= nums.length <= 3000", "-10^5 <= nums[i] <= 10^5"],
        "examples": [
            {"input": "nums = [-1,0,1,2,-1,-4]", "output": "[[-1,-1,2],[-1,0,1]]", "explanation": "Distinct triplets summing to 0."}
        ],
        "starter_code": {
            "python": "def threeSum(nums: list[int]) -> list[list[int]]:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Container With Most Water",
        "slug": "container-with-most-water",
        "difficulty": "Medium",
        "topics": ["Array", "Two Pointers", "Greedy"],
        "patterns": ["Two Pointers"],
        "description": "You are given an integer array `height` of length `n`. There are `n` vertical lines drawn such that the two endpoints of the `i`-th line are `(i, 0)` and `(i, height[i])`.\n\nFind two lines that together with the x-axis form a container, such that the container contains the most water.",
        "constraints": ["n == height.length", "2 <= n <= 10^5", "0 <= height[i] <= 10^4"],
        "examples": [
            {"input": "height = [1,8,6,2,5,4,8,3,7]", "output": "49", "explanation": "The max area of water is 49."}
        ],
        "starter_code": {
            "python": "def maxArea(height: list[int]) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Longest Substring Without Repeating Characters",
        "slug": "longest-substring-without-repeating-characters",
        "difficulty": "Medium",
        "topics": ["Hash Table", "String", "Sliding Window"],
        "patterns": ["Sliding Window"],
        "description": "Given a string `s`, find the length of the longest substring without repeating characters.",
        "constraints": ["0 <= s.length <= 5 * 10^4", "s consists of English letters, digits, symbols and spaces."],
        "examples": [
            {"input": "s = \"abcabcbb\"", "output": "3", "explanation": "The answer is \"abc\", with the length of 3."}
        ],
        "starter_code": {
            "python": "def lengthOfLongestSubstring(s: str) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Longest Repeating Character Replacement",
        "slug": "longest-repeating-character-replacement",
        "difficulty": "Medium",
        "topics": ["Hash Table", "String", "Sliding Window"],
        "patterns": ["Sliding Window"],
        "description": "You are given a string `s` and an integer `k`. You can choose any character of the string and change it to any other uppercase English character. You can perform this operation at most `k` times.\n\nReturn the length of the longest substring containing the same letter you can get after performing the above operations.",
        "constraints": ["1 <= s.length <= 10^5", "s consists of only uppercase English letters.", "0 <= k <= s.length"],
        "examples": [
            {"input": "s = \"ABAB\", k = 2", "output": "4", "explanation": "Replace two 'A's with 'B's or vice versa."}
        ],
        "starter_code": {
            "python": "def characterReplacement(s: str, k: int) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Minimum Window Substring",
        "slug": "minimum-window-substring",
        "difficulty": "Hard",
        "topics": ["Hash Table", "String", "Sliding Window"],
        "patterns": ["Sliding Window"],
        "description": "Given two strings `s` and `t` of lengths `m` and `n` respectively, return the minimum window substring of `s` such that every character in `t` (including duplicates) is included in the window.",
        "constraints": ["m == s.length", "n == t.length", "1 <= m, n <= 10^5"],
        "examples": [
            {"input": "s = \"ADOBECODEBANC\", t = \"ABC\"", "output": "\"BANC\"", "explanation": "Minimum window string is \"BANC\"."}
        ],
        "starter_code": {
            "python": "def minWindow(s: str, t: str) -> str:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Valid Parentheses",
        "slug": "valid-parentheses",
        "difficulty": "Easy",
        "topics": ["String", "Stack"],
        "patterns": ["Stack"],
        "description": "Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.\n\nAn input string is valid if:\n1. Open brackets must be closed by the same type of brackets.\n2. Open brackets must be closed in the correct order.",
        "constraints": ["1 <= s.length <= 10^4", "s consists of parentheses only '()[]{}'."],
        "examples": [
            {"input": "s = \"()[]{}\"", "output": "true", "explanation": "All brackets matched correctly."}
        ],
        "starter_code": {
            "python": "def isValid(s: str) -> bool:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Min Stack",
        "slug": "min-stack",
        "difficulty": "Medium",
        "topics": ["Stack", "Design"],
        "patterns": ["Stack"],
        "description": "Design a stack that supports push, pop, top, and retrieving the minimum element in constant time.",
        "constraints": ["-2^31 <= val <= 2^31 - 1", "Methods pop, top and getMin will always be called on non-empty stacks."],
        "examples": [
            {"input": "[\"MinStack\",\"push\",\"push\",\"push\",\"getMin\",\"pop\",\"top\",\"getMin\"]\n[[],[-2],[0],[-3],[],[],[],[]]", "output": "[null,null,null,null,-3,null,0,-2]", "explanation": "Standard Min Stack operations."}
        ],
        "starter_code": {
            "python": "class MinStack:\n    def __init__(self):\n        pass\n\n    def push(self, val: int) -> None:\n        pass\n\n    def pop(self) -> None:\n        pass\n\n    def top(self) -> int:\n        pass\n\n    def getMin(self) -> int:\n        pass"
        }
    },
    {
        "title": "Binary Search",
        "slug": "binary-search",
        "difficulty": "Easy",
        "topics": ["Array", "Binary Search"],
        "patterns": ["Binary Search"],
        "description": "Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, then return its index. Otherwise, return `-1`.",
        "constraints": ["1 <= nums.length <= 10^4", "-10^4 < nums[i], target < 10^4", "nums is sorted in ascending order."],
        "examples": [
            {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4", "explanation": "9 exists in nums and its index is 4."}
        ],
        "starter_code": {
            "python": "def search(nums: list[int], target: int) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Search in Rotated Sorted Array",
        "slug": "search-in-rotated-sorted-array",
        "difficulty": "Medium",
        "topics": ["Array", "Binary Search"],
        "patterns": ["Modified Binary Search"],
        "description": "There is an integer array `nums` sorted in ascending order (with distinct values). Given the array `nums` after possible rotation and an integer `target`, return the index of `target` if it is in `nums`, or `-1` if it is not in `nums`.",
        "constraints": ["1 <= nums.length <= 5000", "-10^4 <= nums[i] <= 10^4", "All values of nums are unique."],
        "examples": [
            {"input": "nums = [4,5,6,7,0,1,2], target = 0", "output": "4", "explanation": "Target 0 is found at index 4."}
        ],
        "starter_code": {
            "python": "def search(nums: list[int], target: int) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Reverse Linked List",
        "slug": "reverse-linked-list",
        "difficulty": "Easy",
        "topics": ["Linked List", "Recursion"],
        "patterns": ["Iterative / Recursive"],
        "description": "Given the head of a singly linked list, reverse the list, and return the reversed list.",
        "constraints": ["The number of nodes in the list is in the range [0, 5000].", "-5000 <= Node.val <= 5000"],
        "examples": [
            {"input": "head = [1,2,3,4,5]", "output": "[5,4,3,2,1]", "explanation": "Reversed linked list."}
        ],
        "starter_code": {
            "python": "# Definition for singly-linked list.\n# class ListNode:\n#     def __init__(self, val=0, next=None):\n#         self.val = val\n#         self.next = next\ndef reverseList(head: Optional[ListNode]) -> Optional[ListNode]:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Linked List Cycle",
        "slug": "linked-list-cycle",
        "difficulty": "Easy",
        "topics": ["Hash Table", "Linked List", "Two Pointers"],
        "patterns": ["Fast and Slow Pointers"],
        "description": "Given `head`, the head of a linked list, determine if the linked list has a cycle in it.",
        "constraints": ["The number of the nodes in the list is in the range [0, 10^4].", "-10^5 <= Node.val <= 10^5"],
        "examples": [
            {"input": "head = [3,2,0,-4], pos = 1", "output": "true", "explanation": "There is a cycle in the linked list, where tail connects to 1st node."}
        ],
        "starter_code": {
            "python": "def hasCycle(head: Optional[ListNode]) -> bool:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Merge Two Sorted Lists",
        "slug": "merge-two-sorted-lists",
        "difficulty": "Easy",
        "topics": ["Linked List", "Recursion"],
        "patterns": ["Two Pointers"],
        "description": "You are given the heads of two sorted linked lists `list1` and `list2`. Merge the two lists into one sorted list. The list should be made by splicing together the nodes of the first two lists.",
        "constraints": ["The number of nodes in both lists is in the range [0, 50].", "-100 <= Node.val <= 100"],
        "examples": [
            {"input": "list1 = [1,2,4], list2 = [1,3,4]", "output": "[1,1,2,3,4,4]", "explanation": "Merged list in sorted order."}
        ],
        "starter_code": {
            "python": "def mergeTwoLists(list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Maximum Depth of Binary Tree",
        "slug": "maximum-depth-of-binary-tree",
        "difficulty": "Easy",
        "topics": ["Tree", "Depth-First Search", "Binary Tree"],
        "patterns": ["DFS / BFS"],
        "description": "Given the root of a binary tree, return its maximum depth. A binary tree's maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.",
        "constraints": ["The number of nodes in the tree is in the range [0, 10^4].", "-100 <= Node.val <= 100"],
        "examples": [
            {"input": "root = [3,9,20,null,null,15,7]", "output": "3", "explanation": "Maximum depth is 3."}
        ],
        "starter_code": {
            "python": "# Definition for a binary tree node.\n# class TreeNode:\n#     def __init__(self, val=0, left=None, right=None):\n#         self.val = val\n#         self.left = left\n#         self.right = right\ndef maxDepth(root: Optional[TreeNode]) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Invert Binary Tree",
        "slug": "invert-binary-tree",
        "difficulty": "Easy",
        "topics": ["Tree", "Depth-First Search", "Binary Tree"],
        "patterns": ["Tree Traversal"],
        "description": "Given the root of a binary tree, invert the tree, and return its root.",
        "constraints": ["The number of nodes in the tree is in the range [0, 100].", "-100 <= Node.val <= 100"],
        "examples": [
            {"input": "root = [4,2,7,1,3,6,9]", "output": "[4,7,2,9,6,3,1]", "explanation": "Binary tree inverted."}
        ],
        "starter_code": {
            "python": "def invertTree(root: Optional[TreeNode]) -> Optional[TreeNode]:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Binary Tree Level Order Traversal",
        "slug": "binary-tree-level-order-traversal",
        "difficulty": "Medium",
        "topics": ["Tree", "Breadth-First Search", "Binary Tree"],
        "patterns": ["BFS Queue"],
        "description": "Given the root of a binary tree, return the level order traversal of its nodes' values. (i.e., from left to right, level by level).",
        "constraints": ["The number of nodes in the tree is in the range [0, 2000].", "-1000 <= Node.val <= 1000"],
        "examples": [
            {"input": "root = [3,9,20,null,null,15,7]", "output": "[[3],[9,20],[15,7]]", "explanation": "Node values grouped by level."}
        ],
        "starter_code": {
            "python": "def levelOrder(root: Optional[TreeNode]) -> list[list[int]]:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Validate Binary Search Tree",
        "slug": "validate-binary-search-tree",
        "difficulty": "Medium",
        "topics": ["Tree", "Depth-First Search", "Binary Search Tree"],
        "patterns": ["In-order Traversal / Range Validation"],
        "description": "Given the root of a binary tree, determine if it is a valid binary search tree (BST).",
        "constraints": ["The number of nodes in the tree is in the range [1, 10^4].", "-2^31 <= Node.val <= 2^31 - 1"],
        "examples": [
            {"input": "root = [2,1,3]", "output": "true", "explanation": "Valid BST structure."}
        ],
        "starter_code": {
            "python": "def isValidBST(root: Optional[TreeNode]) -> bool:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Kth Smallest Element in a BST",
        "slug": "kth-smallest-element-in-a-bst",
        "difficulty": "Medium",
        "topics": ["Tree", "Depth-First Search", "Binary Search Tree"],
        "patterns": ["In-order Traversal"],
        "description": "Given the root of a binary search tree, and an integer `k`, return the `k`-th smallest value (1-indexed) of all the values of the nodes in the tree.",
        "constraints": ["The number of nodes in the tree is n.", "1 <= k <= n <= 10^4", "0 <= Node.val <= 10^4"],
        "examples": [
            {"input": "root = [3,1,4,null,2], k = 1", "output": "1", "explanation": "1st smallest element is 1."}
        ],
        "starter_code": {
            "python": "def kthSmallest(root: Optional[TreeNode], k: int) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Number of Islands",
        "slug": "number-of-islands",
        "difficulty": "Medium",
        "topics": ["Array", "Depth-First Search", "Breadth-First Search", "Graphs"],
        "patterns": ["Grid Graph DFS/BFS"],
        "description": "Given an `m x n` 2D binary grid `grid` which represents a map of `'1'`s (land) and `'0'`s (water), return the number of islands.\n\nAn island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.",
        "constraints": ["m == grid.length", "n == grid[i].length", "1 <= m, n <= 300", "grid[i][j] is '0' or '1'."],
        "examples": [
            {"input": "grid = [[\"1\",\"1\",\"1\",\"1\",\"0\"],[\"1\",\"1\",\"0\",\"1\",\"0\"],[\"1\",\"1\",\"0\",\"0\",\"0\"],[\"0\",\"0\",\"0\",\"0\",\"0\"]]", "output": "1", "explanation": "1 island found."}
        ],
        "starter_code": {
            "python": "def numIslands(grid: list[list[str]]) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Clone Graph",
        "slug": "clone-graph",
        "difficulty": "Medium",
        "topics": ["Hash Table", "Depth-First Search", "Breadth-First Search", "Graphs"],
        "patterns": ["Graph Traversal + Hash Map"],
        "description": "Given a reference of a node in a connected undirected graph, return a deep copy (clone) of the graph.",
        "constraints": ["The number of nodes in the graph is in the range [0, 100].", "1 <= Node.val <= 100"],
        "examples": [
            {"input": "adjList = [[2,4],[1,3],[2,4],[1,3]]", "output": "[[2,4],[1,3],[2,4],[1,3]]", "explanation": "Cloned graph structure."}
        ],
        "starter_code": {
            "python": "# Definition for a Node.\n# class Node:\n#     def __init__(self, val = 0, neighbors = None):\n#         self.val = val\n#         self.neighbors = neighbors if neighbors is not None else []\ndef cloneGraph(node: Optional['Node']) -> Optional['Node']:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Course Schedule",
        "slug": "course-schedule",
        "difficulty": "Medium",
        "topics": ["Depth-First Search", "Breadth-First Search", "Graphs", "Topological Sort"],
        "patterns": ["Cycle Detection / Topological Sort"],
        "description": "There are a total of `numCourses` courses you have to take, labeled from `0` to `numCourses - 1`. You are given an array `prerequisites` where `prerequisites[i] = [a, b]` indicates that you must take course `b` first if you want to take course `a`.\n\nReturn `true` if you can finish all courses. Otherwise, return `false`.",
        "constraints": ["1 <= numCourses <= 2000", "0 <= prerequisites.length <= 5000", "prerequisites[i].length == 2"],
        "examples": [
            {"input": "numCourses = 2, prerequisites = [[1,0]]", "output": "true", "explanation": "Take course 0 before course 1."}
        ],
        "starter_code": {
            "python": "def canFinish(numCourses: int, prerequisites: list[list[int]]) -> bool:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Climbing Stairs",
        "slug": "climbing-stairs",
        "difficulty": "Easy",
        "topics": ["Math", "Dynamic Programming"],
        "patterns": ["DP / Fibonacci"],
        "description": "You are climbing a staircase. It takes `n` steps to reach the top.\n\nEach time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
        "constraints": ["1 <= n <= 45"],
        "examples": [
            {"input": "n = 2", "output": "2", "explanation": "1 step + 1 step, or 2 steps."}
        ],
        "starter_code": {
            "python": "def climbStairs(n: int) -> int:\n    # Write your solution here\n    pass"
        }
    },
    {
        "title": "Coin Change",
        "slug": "coin-change",
        "difficulty": "Medium",
        "topics": ["Array", "Dynamic Programming"],
        "patterns": ["Unbounded Knapsack / DP"],
        "description": "You are given an integer array `coins` representing coins of different denominations and an integer `amount` representing a total amount of money.\n\nReturn the fewest number of coins that you need to make up that amount. If that amount of money cannot be made up by any combination of the coins, return `-1`.",
        "constraints": ["1 <= coins.length <= 12", "1 <= coins[i] <= 2^31 - 1", "0 <= amount <= 10^4"],
        "examples": [
            {"input": "coins = [1,2,5], amount = 11", "output": "3", "explanation": "11 = 5 + 5 + 1."}
        ],
        "starter_code": {
            "python": "def coinChange(coins: list[int], amount: int) -> int:\n    # Write your solution here\n    pass"
        }
    }
]

class Command(BaseCommand):
    help = 'Seeds database with 30 initial DSA problems and test cases'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        tc_count = 0

        for problem_data in SEED_PROBLEMS:
            problem, created = Problem.objects.update_or_create(
                slug=problem_data['slug'],
                defaults=problem_data
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

            # Seed TestCases for problem
            for idx, ex in enumerate(problem_data.get('examples', [])):
                tc, tc_created = TestCase.objects.update_or_create(
                    problem=problem,
                    input_data=ex['input'],
                    defaults={
                        'expected_output': ex['output'],
                        'is_public': True
                    }
                )
                if tc_created:
                    tc_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed 30 DSA problems & {tc_count} test cases! (Created: {created_count}, Updated: {updated_count})'
            )
        )
