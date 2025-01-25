from typing import List
from collections import deque

class Solution:
    def makesquare(self, matchsticks: List[int]) -> bool:
        perimeter = sum(matchsticks)
        if perimeter % 4 != 0:
            return False

        sideLen = int(sum(matchsticks)/4)

        groups = []
        queue = deque([matchsticks])
        def dfs(matchsticks, target, group):
            nonlocal groups
            if target == 0:
                groups.append(group)
                queue.append(matchsticks)
                return matchsticks

            i = 0
            while matchsticks[i] < target:
                newMatchsticks = matchsticks[:i] + matchsticks[i + 1:]
                group.append(matchsticks[i])
                dfs(newMatchsticks, target - matchsticks[i], group)
                i += 1
            return

        while queue:
            thisSeq = queue.popleft()
            if not dfs(thisSeq, sideLen, []):
                return True

        return False

print(Solution().makesquare([1,1,2,2,2]))
        
            
        







