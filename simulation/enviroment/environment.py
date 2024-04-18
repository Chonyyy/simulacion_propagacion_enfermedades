from simulation.agents.agents import Agent
from simulation.agents.agent_arquitecture import BehaviorLayer, LocalPlanningLayer, Knowledge
from simulation.epidemic.epidemic_model import EpidemicModel
from simulation.enviroment.sim_nodes import CitizenPerceptionNode as CPNode
from simulation.enviroment.sim_nodes import BlockNode, Hospital, HouseNode, PublicPlace, BusStop, Workspace
from simulation.enviroment.map import Terrain
from typing import Tuple, List
import random
from simulation.enviroment.graph import Graph
import logging

logger = logging.getLogger(__name__)

class Environment:
    """
    Class representing the simulation environment.

    Attributes:
        map (Terrain): The terrain of the simulation.
        agents (List[Agent]): The list of agents in the environment.
        epidemic_model (EpidemicModel): The epidemic model for the simulation.
    """
    def __init__(self, num_agents: int, epidemic_model: EpidemicModel, map: Terrain):
        """
        Initialize the environment.

        Args:
            num_agents (int): The number of agents to initialize in the environment.
            epidemic_model (EpidemicModel): The epidemic model for the simulation.
            map (Terrain): The terrain of the simulation.
        """
        self.map = map    
        self.agents: List[Agent] = []
        self.epidemic_model = epidemic_model
        logger.debug('=== Initializing Agents ===')
        self.initialize_citizen_agents(num_agents)

    def initialize_citizen_agents(self, num_agents: int) -> None:
        """
        Initialize agents within the environment.

        Args:
            num_agents (int): The number of agents to initialize.
        """
        infected_agents = random.randint(0, int(num_agents/2))
        for i in range(num_agents):
            mind_map = self.generate_citizen_mind_map()
            kb = self._initialize_places_for_agents()
            
            agents_wi  = WorldInterface(self.map, mind_map, kb)
            agents_bbc = BehaviorLayer(mind_map, kb)
            agents_pbc = LocalPlanningLayer(mind_map, kb)
            
            agent = Agent(
                unique_id=i, 
                mind_map=mind_map, 
                wi_component=agents_wi,
                bb_component=agents_bbc,
                lp_component=agents_pbc,
                knowledge_base=kb
                )
            
            if i < infected_agents:
                self.epidemic_model._infect_citizen(agent)

            location = random.choice(list(self.map.keys()))
            self.add_agent(agent, location)

    def add_agent(self, agent: Agent, pos: int) -> None:
        """
        Add an agent to the environment at a specified location.

        Args:
            agent (Agent): The agent to add.
            pos (int): The position of the agent's location.
        """
        agent.location = pos
        self.map[pos].agent_list.append(agent.unique_id)
        self.agents.append(agent)

    def generate_citizen_mind_map(self) -> Graph:
        """
        Generate a mind map for a citizen agent.

        Returns:
            Graph: The generated mind map.
        """
        mind_map = Graph()
        for node_id in self.map.keys():
            old_node = self.map[node_id]
            if isinstance(old_node, BlockNode):
                node_type = 'block'
            elif isinstance(old_node, Hospital):
                node_type = 'hospital'
            elif isinstance(old_node, Workspace):
                node_type = 'work_space'
            elif isinstance(old_node, BusStop):
                node_type = 'bus_stop'
            elif isinstance(old_node, PublicPlace):
                node_type = 'public_space'
            elif isinstance(old_node, HouseNode):
                node_type = 'house'
            else:
                raise ValueError(f'node of type unknown{type(old_node)}')
            
            new_node = CPNode(old_node.addr, old_node.id, node_type)
            mind_map.add_node(new_node)

        mind_map.edges = self.map.graph.edges.copy()
        
        return mind_map

    def get_neighbors(self, agent: Agent) -> List[Agent]:
        """
        Get the neighbors of an agent.

        Args:
            agent (Agent): The agent to get neighbors for.

        Returns:
            List[Agent]: A list of neighboring agents.
        """
        agents_node = self.map.nodes[agent.location]
        return [self.agents[agent_id] for agent_id in agents_node.agent_list if agent_id != agent.unique_id]

    def step(self, step_num: int) -> None:
        """
        Perform a simulation step, where agents take actions.

        Args:
            step_num (int): The current step number of the simulation.
        """
        for agent in random.sample(self.agents, len(self.agents)):
            agent.step(step_num)

    def _initialize_places_for_agents(self):
        kb = Knowledge()
        house_id = random.choice(self.map.houses)
        kb.add_home(house_id)
        is_medic = random.choice([True, False])
        
        if is_medic:
            work_id = random.choice(self.map.hospitals)
            kb.add_work_place(work_id)
            kb.add_is_medical_personnel(True)
        else:
            work_id = random.choice(self.map.works)
            kb.add_work_place(work_id)
            kb.add_is_medical_personnel(False)
            
        return kb
        

class WorldInterface:
    """
    Class representing the world interface for an agent.

    Attributes:
        map (Graph): The map of the simulation.
        agent_mind_map (Graph): The mind map of the agent.
        agent_kb (Knowledge): The knowledge base of the agent.
    """
    def __init__(self, map: Graph, agent_mind_map: Graph, knowledge_base: Knowledge) -> None:
        self.map = map
        self.agent_mind_map = agent_mind_map
        self.agent_kb = knowledge_base

    def act(self, agent: Agent, action: str, parameters: list = None) -> None:
        """
        Perform an action for an agent.

        Args:
            agent (Agent): The agent performing the action.
            action (str): The action to perform.
            parameters (list): The parameters for the action.
        """
        if isinstance(parameters, int):
            parametersList = []
            parametersList.append(parameters)
            parameters = parametersList
            
        if action == 'move':
            logger.info(f'Agent {agent.unique_id} is moving to {parameters[0]}')
            self.move_agent(agent, parameters)
            
        elif action == 'use_mask':
            logger.info(f'Agent {agent.unique_id} is using mask')
            agent.masked = True 
            
        elif action == 'remove_mask':
            logger.info(f'Agent {agent.unique_id} is removing mask')
            agent.masked = False 
        
        elif action == 'vaccinate':
            logger.info(f'Agent {agent.unique_id} is vaccinated')
            agent.vaccinated = True
            
        elif action == 'sleep':
            logger.info(f'Agent {agent.unique_id} is sleeping')
        
        elif action == 'wake_up':
            logger.info(f'Agent {agent.unique_id} is wake up')
        
        else:
            logger.error(f'Action {action} not recognized')

    def comunicate(self, emiter, reciever, message) -> None:
        """
        Communicate a message from one agent to another.

        Args:
            emiter (Agent): The agent sending the message.
            reciever (Agent): The agent receiving the message.
            message (str): The message to send.
        """
        raise NotImplementedError

    def recieve_comunication(self, agent, message) -> None:
        """
        Receive a communication from another agent.

        Args:
            agent (Agent): The agent receiving the communication.
            message (str): The received message.
        """
        raise NotImplementedError

    def percieve(self, agent: Agent, step_num: int) -> dict:
        """
        Perceive the environment around an agent.

        Args:
            agent (Agent): The agent perceiving the environment.
            step_num (int): The current step number of the simulation.

        Returns:
            dict: A dictionary of perceived environments.
        """
        def density_classifier(node_population, node_capacity):
            node_density = node_population/node_capacity
            if node_density < 0.5:
                return 'low'
            elif node_density < 0.8:
                return 'medium'
            elif node_density <= 1.0:
                return 'high'
            else:
                return 'very_high'
        
        new_perception = {}

        current_node = self.map[agent.location]
        current_node_perception = CPNode(current_node.addr, current_node.id, density_classifier(len(current_node.agent_list), current_node.capacity))
        new_perception[current_node.addr] = current_node_perception

        for neighbor_key in self.map.graph.get_neighbors(agent.location):
            neighbor_node = self.map[neighbor_key]
            node_density = density_classifier(len(neighbor_node.agent_list), neighbor_node.capacity)
            new_perception[neighbor_node.addr] = CPNode(neighbor_node.addr, neighbor_key, node_density)

        return new_perception

    def move_agent(self, agent: Agent, pos: int) -> None:
        """
        Move an agent to a new location.

        Args:
            agent (Agent): The agent to move.
            pos (int): The new location for the agent.
        """
        pos = tuple(pos)
        prev_location = agent.location

        prev_neighbors = self.map.graph.get_neighbors(prev_location)

        if pos not in prev_neighbors:
            logger.error(f'Agent {agent.unique_id} cannot move to {pos} from {prev_location}')
            return
        
        self.map.nodes[prev_location].agent_list.remove(agent.unique_id)

        agent.location = pos
        self.map.nodes[pos].agent_list.append(agent.unique_id)
