from multiprocessing import Pool, Manager
from subprocess import Popen
import time
import csv
import sys
import os
from tempfile import mktemp

inputs = [('https://github.com/apache/distributedlog', 'http:\\issues.apache.org\\jira\\projects\\DL'), ('https://github.com/apache/maven-indexer', 'http:\\issues.apache.org\\jira\\projects\\MINDEXER'), ('https://github.com/apache/rampart', 'http:\\issues.apache.org\\jira\\projects\\RAMPART'), ('https://github.com/apache/commons-functor', 'http:\\issues.apache.org\\jira\\projects\\FUNCTOR'), ('https://github.com/apache/velocity-tools', 'http:\\issues.apache.org\\jira\\projects\\VELTOOLS'), ('https://github.com/apache/commons-fileupload', 'http:\\issues.apache.org\\jira\\projects\\FILEUPLOAD'), ('https://github.com/apache/crunch', 'http:\\issues.apache.org\\jira\\projects\\CRUNCH'), ('https://github.com/apache/johnzon', 'http:\\issues.apache.org\\jira\\projects\\JOHNZON'), ('https://github.com/apache/joshua', 'http:\\issues.apache.org\\jira\\projects\\JOSHUA'), ('https://github.com/apache/marmotta', 'http:\\issues.apache.org\\jira\\projects\\MARMOTTA'), ('https://github.com/apache/qpid', 'http:\\issues.apache.org\\jira\\projects\\QPID'), ('https://github.com/apache/mnemonic', 'http:\\issues.apache.org\\jira\\projects\\MNEMONIC'), ('https://github.com/apache/james-jdkim', 'http:\\issues.apache.org\\jira\\projects\\JDKIM'), ('https://github.com/apache/maven-patch-plugin', 'http:\\issues.apache.org\\jira\\projects\\MPATCH'), ('https://github.com/apache/commons-dbcp', 'http:\\issues.apache.org\\jira\\projects\\DBCP'), ('https://github.com/apache/commons-crypto', 'http:\\issues.apache.org\\jira\\projects\\CRYPTO'), ('https://github.com/apache/commons-jexl', 'http:\\issues.apache.org\\jira\\projects\\JEXL'), ('https://github.com/apache/curator', 'http:\\issues.apache.org\\jira\\projects\\CURATOR'), ('https://github.com/apache/maven-wagon', 'http:\\issues.apache.org\\jira\\projects\\WAGON'), ('https://github.com/apache/maven-jlink-plugin', 'http:\\issues.apache.org\\jira\\projects\\MJLINK'), ('https://github.com/apache/commons-weaver', 'http:\\issues.apache.org\\jira\\projects\\WEAVER'), ('https://github.com/apache/qpid-jms', 'http:\\issues.apache.org\\jira\\projects\\QPIDJMS'), ('https://github.com/apache/pulsar', 'http:\\issues.apache.org\\jira\\projects\\PULSAR'), ('https://github.com/apache/directmemory', 'http:\\issues.apache.org\\jira\\projects\\DIRECTMEMORY'), ('https://github.com/apache/nifi', 'http:\\issues.apache.org\\jira\\projects\\NIFI'), ('https://github.com/apache/commons-email', 'http:\\issues.apache.org\\jira\\projects\\EMAIL'), ('https://github.com/apache/activemq-openwire', 'http:\\issues.apache.org\\jira\\projects\\OPENWIRE'), ('https://github.com/apache/maven-javadoc-plugin', 'http:\\issues.apache.org\\jira\\projects\\MJAVADOC'), ('https://github.com/apache/mina', 'http:\\issues.apache.org\\jira\\projects\\DIRMINA'), ('https://github.com/apache/juneau', 'http:\\issues.apache.org\\jira\\projects\\JUNEAU'), ('https://github.com/apache/maven-resolver', 'http:\\issues.apache.org\\jira\\projects\\MRESOLVER'), ('https://github.com/apache/jackrabbit-oak', 'http:\\issues.apache.org\\jira\\projects\\OAK'), ('https://github.com/apache/commons-validator', 'http:\\issues.apache.org\\jira\\projects\\VALIDATOR'), ('https://github.com/apache/james-jspf', 'http:\\issues.apache.org\\jira\\projects\\JSPF'), ('https://github.com/apache/tiles', 'http:\\issues.apache.org\\jira\\projects\\TILES'), ('https://github.com/apache/maven-dependency-plugin', 'http:\\issues.apache.org\\jira\\projects\\MDEP'), ('https://github.com/apache/zookeeper', 'http:\\issues.apache.org\\jira\\projects\\ZOOKEEPER'), ('https://github.com/apache/airavata', 'http:\\issues.apache.org\\jira\\projects\\AIRAVATA'), ('https://github.com/apache/maven-rar-plugin', 'http:\\issues.apache.org\\jira\\projects\\MRAR'), ('https://github.com/apache/rocketmq', 'http:\\issues.apache.org\\jira\\projects\\ROCKETMQ'), ('https://github.com/apache/openejb', 'http:\\issues.apache.org\\jira\\projects\\OPENEJB'), ('https://github.com/apache/submarine', 'http:\\issues.apache.org\\jira\\projects\\SUBMARINE'), ('https://github.com/apache/stanbol', 'http:\\issues.apache.org\\jira\\projects\\STANBOL'), ('https://github.com/apache/nifi-registry', 'http:\\issues.apache.org\\jira\\projects\\NIFIREG'), ('https://github.com/apache/maven-remote-resources-plugin', 'http:\\issues.apache.org\\jira\\projects\\MRRESOURCES'), ('https://github.com/apache/hadoop-common', 'http:\\issues.apache.org\\jira\\projects\\HADOOP'), ('https://github.com/apache/openjpa', 'http:\\issues.apache.org\\jira\\projects\\OPENJPA'), ('https://github.com/apache/syncope', 'http:\\issues.apache.org\\jira\\projects\\SYNCOPE'), ('https://github.com/apache/servicemix', 'http:\\issues.apache.org\\jira\\projects\\SM'), ('https://github.com/apache/phoenix-omid', 'http:\\issues.apache.org\\jira\\projects\\OMID'), ('https://github.com/apache/phoenix-tephra', 'http:\\issues.apache.org\\jira\\projects\\TEPHRA'), ('https://github.com/apache/myfaces-trinidad', 'http:\\issues.apache.org\\jira\\projects\\TRINIDAD'), ('https://github.com/apache/jena', 'http:\\issues.apache.org\\jira\\projects\\JENA'), ('https://github.com/apache/commons-logging', 'http:\\issues.apache.org\\jira\\projects\\LOGGING'), ('https://github.com/apache/maven-pdf-plugin', 'http:\\issues.apache.org\\jira\\projects\\MPDF'), ('https://github.com/apache/maven-archetype', 'http:\\issues.apache.org\\jira\\projects\\ARCHETYPE'), ('https://github.com/apache/hama', 'http:\\issues.apache.org\\jira\\projects\\HAMA'), ('https://github.com/apache/archiva', 'http:\\issues.apache.org\\jira\\projects\\MRM'), ('https://github.com/apache/commons-pool', 'http:\\issues.apache.org\\jira\\projects\\POOL'), ('https://github.com/apache/plc4x', 'http:\\issues.apache.org\\jira\\projects\\PLC4X'), ('https://github.com/apache/oltu', 'http:\\issues.apache.org\\jira\\projects\\OLTU'), ('https://github.com/apache/ftpserver', 'http:\\issues.apache.org\\jira\\projects\\FTPSERVER'), ('https://github.com/apache/cloudstack', 'http:\\issues.apache.org\\jira\\projects\\CLOUDSTACK'), ('https://github.com/apache/maven-verifier-plugin', 'http:\\issues.apache.org\\jira\\projects\\MVERIFIER'), ('https://github.com/apache/metron', 'http:\\issues.apache.org\\jira\\projects\\METRON'), ('https://github.com/apache/wicket', 'http:\\issues.apache.org\\jira\\projects\\WICKET'), ('https://github.com/apache/aries', 'http:\\issues.apache.org\\jira\\projects\\ARIES'), ('https://github.com/apache/accumulo', 'http:\\issues.apache.org\\jira\\projects\\ACCUMULO'), ('https://github.com/apache/maven-shade-plugin', 'http:\\issues.apache.org\\jira\\projects\\MSHADE'), ('https://github.com/apache/unomi', 'http:\\issues.apache.org\\jira\\projects\\UNOMI'), ('https://github.com/apache/maven-gpg-plugin', 'http:\\issues.apache.org\\jira\\projects\\MGPG'), ('https://github.com/apache/maven-toolchains-plugin', 'http:\\issues.apache.org\\jira\\projects\\MTOOLCHAINS'), ('https://github.com/apache/maven-jdeprscan-plugin', 'http:\\issues.apache.org\\jira\\projects\\MJDEPRSCAN'), ('https://github.com/apache/flink', 'http:\\issues.apache.org\\jira\\projects\\FLINK'), ('https://github.com/apache/commons-lang', 'http:\\issues.apache.org\\jira\\projects\\LANG'), ('https://github.com/apache/mahout', 'http:\\issues.apache.org\\jira\\projects\\MAHOUT'), ('https://github.com/apache/metamodel', 'http:\\issues.apache.org\\jira\\projects\\METAMODEL'), ('https://github.com/apache/eagle', 'http:\\issues.apache.org\\jira\\projects\\EAGLE'), ('https://github.com/apache/maven-help-plugin', 'http:\\issues.apache.org\\jira\\projects\\MPH'), ('https://github.com/apache/tika', 'http:\\issues.apache.org\\jira\\projects\\TIKA'), ('https://github.com/apache/ambari', 'http:\\issues.apache.org\\jira\\projects\\AMBARI'), ('https://github.com/apache/vxquery', 'http:\\issues.apache.org\\jira\\projects\\VXQUERY'), ('https://github.com/apache/maven-jdeps-plugin', 'http:\\issues.apache.org\\jira\\projects\\MJDEPS'), ('https://github.com/apache/commons-rng', 'http:\\issues.apache.org\\jira\\projects\\RNG'), ('https://github.com/apache/helix', 'http:\\issues.apache.org\\jira\\projects\\HELIX'), ('https://github.com/apache/tinkerpop', 'http:\\issues.apache.org\\jira\\projects\\TINKERPOP'), ('https://github.com/apache/isis', 'http:\\issues.apache.org\\jira\\projects\\ISIS'), ('https://github.com/apache/synapse', 'http:\\issues.apache.org\\jira\\projects\\SYNAPSE'), ('https://github.com/apache/hcatalog', 'http:\\issues.apache.org\\jira\\projects\\HCATALOG'), ('https://github.com/apache/asterixdb', 'http:\\issues.apache.org\\jira\\projects\\ASTERIXDB'), ('https://github.com/apache/commons-proxy', 'http:\\issues.apache.org\\jira\\projects\\PROXY'), ('https://github.com/apache/sandesha', 'http:\\issues.apache.org\\jira\\projects\\SAND'), ('https://github.com/apache/shindig', 'http:\\issues.apache.org\\jira\\projects\\SHINDIG'), ('https://github.com/apache/commons-imaging', 'http:\\issues.apache.org\\jira\\projects\\IMAGING'), ('https://github.com/apache/openwebbeans', 'http:\\issues.apache.org\\jira\\projects\\OWB'), ('https://github.com/apache/maven-plugin-testing', 'http:\\issues.apache.org\\jira\\projects\\MPLUGINTESTING'), ('https://github.com/apache/tomee', 'http:\\issues.apache.org\\jira\\projects\\TOMEE'), ('https://github.com/apache/activemq-cli-tools', 'http:\\issues.apache.org\\jira\\projects\\AMQCLI'), ('https://github.com/apache/geronimo', 'http:\\issues.apache.org\\jira\\projects\\GERONIMO'), ('https://github.com/apache/juddi', 'http:\\issues.apache.org\\jira\\projects\\JUDDI'), ('https://github.com/apache/maven-project-info-reports-plugin', 'http:\\issues.apache.org\\jira\\projects\\MPIR'), ('https://github.com/apache/commons-net', 'http:\\issues.apache.org\\jira\\projects\\NET'), ('https://github.com/apache/odftoolkit', 'http:\\issues.apache.org\\jira\\projects\\ODFTOOLKIT'), ('https://github.com/apache/maven-changelog-plugin', 'http:\\issues.apache.org\\jira\\projects\\MCHANGELOG'), ('https://github.com/apache/bval', 'http:\\issues.apache.org\\jira\\projects\\BVAL'), ('https://github.com/apache/cayenne', 'http:\\issues.apache.org\\jira\\projects\\CAY'), ('https://github.com/apache/chainsaw', 'http:\\issues.apache.org\\jira\\projects\\CHAINSAW'), ('https://github.com/apache/cxf-fediz', 'http:\\issues.apache.org\\jira\\projects\\FEDIZ'), ('https://github.com/apache/commons-beanutils', 'http:\\issues.apache.org\\jira\\projects\\BEANUTILS'), ('https://github.com/apache/commons-ognl', 'http:\\issues.apache.org\\jira\\projects\\OGNL'), ('https://github.com/apache/tajo', 'http:\\issues.apache.org\\jira\\projects\\TAJO'), ('https://github.com/apache/cxf', 'http:\\issues.apache.org\\jira\\projects\\CXF'), ('https://github.com/apache/james-jsieve', 'http:\\issues.apache.org\\jira\\projects\\JSIEVE'), ('https://github.com/apache/phoenix', 'http:\\issues.apache.org\\jira\\projects\\PHOENIX'), ('https://github.com/apache/pivot', 'http:\\issues.apache.org\\jira\\projects\\PIVOT'), ('https://github.com/apache/maven-resources-plugin', 'http:\\issues.apache.org\\jira\\projects\\MRESOURCES'), ('https://github.com/apache/gora', 'http:\\issues.apache.org\\jira\\projects\\GORA'), ('https://github.com/apache/commons-io', 'http:\\issues.apache.org\\jira\\projects\\IO'), ('https://github.com/apache/activemq', 'http:\\issues.apache.org\\jira\\projects\\AMQ'), ('https://github.com/apache/maven-jar-plugin', 'http:\\issues.apache.org\\jira\\projects\\MJAR'), ('https://github.com/apache/commons-collections', 'http:\\issues.apache.org\\jira\\projects\\COLLECTIONS'), ('https://github.com/apache/manifoldcf', 'http:\\issues.apache.org\\jira\\projects\\CONNECTORS'), ('https://github.com/apache/griffin', 'http:\\issues.apache.org\\jira\\projects\\GRIFFIN'), ('https://github.com/apache/chukwa', 'http:\\issues.apache.org\\jira\\projects\\CHUKWA'), ('https://github.com/apache/oodt', 'http:\\issues.apache.org\\jira\\projects\\OODT'), ('https://github.com/apache/kalumet', 'http:\\issues.apache.org\\jira\\projects\\KALUMET'), ('https://github.com/apache/tez', 'http:\\issues.apache.org\\jira\\projects\\TEZ'), ('https://github.com/apache/maven-ejb-plugin', 'http:\\issues.apache.org\\jira\\projects\\MEJB'), ('https://github.com/apache/deltaspike', 'http:\\issues.apache.org\\jira\\projects\\DELTASPIKE'), ('https://github.com/apache/commons-jelly', 'http:\\issues.apache.org\\jira\\projects\\JELLY'), ('https://github.com/apache/jclouds', 'http:\\issues.apache.org\\jira\\projects\\JCLOUDS'), ('https://github.com/apache/ranger', 'http:\\issues.apache.org\\jira\\projects\\RANGER'), ('https://github.com/apache/activemq-artemis', 'http:\\issues.apache.org\\jira\\projects\\ARTEMIS'), ('https://github.com/apache/sentry', 'http:\\issues.apache.org\\jira\\projects\\SENTRY'), ('https://github.com/apache/activemq-apollo', 'http:\\issues.apache.org\\jira\\projects\\APLO'), ('https://github.com/apache/rya', 'http:\\issues.apache.org\\jira\\projects\\RYA'), ('https://github.com/apache/commons-codec', 'http:\\issues.apache.org\\jira\\projects\\CODEC'), ('https://github.com/apache/ddlutils', 'http:\\issues.apache.org\\jira\\projects\\DDLUTILS'), ('https://github.com/apache/commons-text', 'http:\\issues.apache.org\\jira\\projects\\TEXT'), ('https://github.com/apache/giraph', 'http:\\issues.apache.org\\jira\\projects\\GIRAPH'), ('https://github.com/apache/bigtop', 'http:\\issues.apache.org\\jira\\projects\\BIGTOP'), ('https://github.com/apache/commons-configuration', 'http:\\issues.apache.org\\jira\\projects\\CONFIGURATION'), ('https://github.com/apache/james-mime4j', 'http:\\issues.apache.org\\jira\\projects\\MIME4J'), ('https://github.com/apache/maven-site-plugin', 'http:\\issues.apache.org\\jira\\projects\\MSITE'), ('https://github.com/apache/opennlp', 'http:\\issues.apache.org\\jira\\projects\\OPENNLP'), ('https://github.com/apache/storm', 'http:\\issues.apache.org\\jira\\projects\\STORM'), ('https://github.com/apache/zeppelin', 'http:\\issues.apache.org\\jira\\projects\\ZEPPELIN'), ('https://github.com/apache/maven-doap-plugin', 'http:\\issues.apache.org\\jira\\projects\\MDOAP'), ('https://github.com/apache/maven-changes-plugin', 'http:\\issues.apache.org\\jira\\projects\\MCHANGES'), ('https://github.com/apache/maven-doxia', 'http:\\issues.apache.org\\jira\\projects\\DOXIA'), ('https://github.com/apache/maven-surefire', 'http:\\issues.apache.org\\jira\\projects\\SUREFIRE'), ('https://github.com/apache/myfaces-test', 'http:\\issues.apache.org\\jira\\projects\\MYFACESTEST'), ('https://github.com/apache/twill', 'http:\\issues.apache.org\\jira\\projects\\TWILL'), ('https://github.com/apache/continuum', 'http:\\issues.apache.org\\jira\\projects\\CONTINUUM'), ('https://github.com/apache/maven-clean-plugin', 'http:\\issues.apache.org\\jira\\projects\\MCLEAN'), ('https://github.com/apache/kylin', 'http:\\issues.apache.org\\jira\\projects\\KYLIN'), ('https://github.com/apache/maven-doxia-tools', 'http:\\issues.apache.org\\jira\\projects\\DOXIATOOLS'), ('https://github.com/apache/jsecurity', 'http:\\issues.apache.org\\jira\\projects\\JSEC'), ('https://github.com/apache/maven-deploy-plugin', 'http:\\issues.apache.org\\jira\\projects\\MDEPLOY'), ('https://github.com/apache/tiles-autotag', 'http:\\issues.apache.org\\jira\\projects\\AUTOTAG'), ('https://github.com/apache/mina-sshd', 'http:\\issues.apache.org\\jira\\projects\\SSHD'), ('https://github.com/apache/maven-compiler-plugin', 'http:\\issues.apache.org\\jira\\projects\\MCOMPILER'), ('https://github.com/apache/maven-install-plugin', 'http:\\issues.apache.org\\jira\\projects\\MINSTALL'), ('https://github.com/apache/sanselan', 'http:\\issues.apache.org\\jira\\projects\\SANSELAN'), ('https://github.com/apache/avro', 'http:\\issues.apache.org\\jira\\projects\\AVRO'), ('https://github.com/apache/commons-compress', 'http:\\issues.apache.org\\jira\\projects\\COMPRESS'), ('https://github.com/apache/hadoop', 'http:\\issues.apache.org\\jira\\projects\\HADOOP'), ('https://github.com/apache/shiro', 'http:\\issues.apache.org\\jira\\projects\\SHIRO'), ('https://github.com/apache/empire-db', 'http:\\issues.apache.org\\jira\\projects\\EMPIREDB'), ('https://github.com/apache/commons-bsf', 'http:\\issues.apache.org\\jira\\projects\\BSF'), ('https://github.com/apache/chemistry', 'http:\\issues.apache.org\\jira\\projects\\CMIS'), ('https://github.com/apache/commons-digester', 'http:\\issues.apache.org\\jira\\projects\\DIGESTER'), ('https://github.com/apache/directory-studio', 'http:\\issues.apache.org\\jira\\projects\\DIRSTUDIO'), ('https://github.com/apache/falcon', 'http:\\issues.apache.org\\jira\\projects\\FALCON'), ('https://github.com/apache/myfaces-tobago', 'http:\\issues.apache.org\\jira\\projects\\TOBAGO'), ('https://github.com/apache/maven-assembly-plugin', 'http:\\issues.apache.org\\jira\\projects\\MASSEMBLY'), ('https://github.com/apache/openmeetings', 'http:\\issues.apache.org\\jira\\projects\\OPENMEETINGS'), ('https://github.com/apache/savan', 'http:\\issues.apache.org\\jira\\projects\\SAVAN'), ('https://github.com/apache/maven-invoker-plugin', 'http:\\issues.apache.org\\jira\\projects\\MINVOKER'), ('https://github.com/apache/pdfbox', 'http:\\issues.apache.org\\jira\\projects\\PDFBOX'), ('https://github.com/apache/maven-jxr', 'http:\\issues.apache.org\\jira\\projects\\JXR'), ('https://github.com/apache/reef', 'http:\\issues.apache.org\\jira\\projects\\REEF'), ('https://github.com/apache/maven-checkstyle-plugin', 'http:\\issues.apache.org\\jira\\projects\\MCHECKSTYLE'), ('https://github.com/apache/maven-war-plugin', 'http:\\issues.apache.org\\jira\\projects\\MWAR'), ('https://github.com/apache/maven-jmod-plugin', 'http:\\issues.apache.org\\jira\\projects\\MJMOD'), ('https://github.com/apache/commons-dbutils', 'http:\\issues.apache.org\\jira\\projects\\DBUTILS'), ('https://github.com/apache/lens', 'http:\\issues.apache.org\\jira\\projects\\LENS'), ('https://github.com/apache/abdera', 'http:\\issues.apache.org\\jira\\projects\\ABDERA'), ('https://github.com/apache/maven-stage-plugin', 'http:\\issues.apache.org\\jira\\projects\\MSTAGE'), ('https://github.com/apache/maven-source-plugin', 'http:\\issues.apache.org\\jira\\projects\\MSOURCES'), ('https://github.com/apache/atlas', 'http:\\issues.apache.org\\jira\\projects\\ATLAS'), ('https://github.com/apache/hive', 'http:\\issues.apache.org\\jira\\projects\\HIVE'), ('https://github.com/apache/maven-plugin-tools', 'http:\\issues.apache.org\\jira\\projects\\MPLUGIN'), ('https://github.com/apache/cxf-xjc-utils', 'http:\\issues.apache.org\\jira\\projects\\CXFXJC'), ('https://github.com/apache/commons-numbers', 'http:\\issues.apache.org\\jira\\projects\\NUMBERS'), ('https://github.com/apache/bookkeeper', 'http:\\issues.apache.org\\jira\\projects\\BOOKKEEPER'), ('https://github.com/apache/karaf', 'http:\\issues.apache.org\\jira\\projects\\KARAF'), ('https://github.com/apache/maven-doxia-sitetools', 'http:\\issues.apache.org\\jira\\projects\\DOXIASITETOOLS'), ('https://github.com/apache/drill', 'http:\\issues.apache.org\\jira\\projects\\DRILL'), ('https://github.com/apache/maven-pmd-plugin', 'http:\\issues.apache.org\\jira\\projects\\MPMD'), ('https://github.com/apache/sis', 'http:\\issues.apache.org\\jira\\projects\\SIS'), ('https://github.com/apache/tiles-request', 'http:\\issues.apache.org\\jira\\projects\\TREQ'), ('https://github.com/apache/commons-chain', 'http:\\issues.apache.org\\jira\\projects\\CHAIN'), ('https://github.com/apache/systemml', 'http:\\issues.apache.org\\jira\\projects\\SYSTEMML'), ('https://github.com/apache/ignite', 'http:\\issues.apache.org\\jira\\projects\\IGNITE'), ('https://github.com/apache/commons-csv', 'http:\\issues.apache.org\\jira\\projects\\CSV'), ('https://github.com/apache/hbase', 'http:\\issues.apache.org\\jira\\projects\\HBASE'), ('https://github.com/apache/maven-antrun-plugin', 'http:\\issues.apache.org\\jira\\projects\\MANTRUN'), ('https://github.com/apache/usergrid', 'http:\\issues.apache.org\\jira\\projects\\USERGRID'), ('https://github.com/apache/commons-jxpath', 'http:\\issues.apache.org\\jira\\projects\\JXPATH'), ('https://github.com/apache/cocoon', 'http:\\issues.apache.org\\jira\\projects\\COCOON'), ('https://github.com/apache/wookie', 'http:\\issues.apache.org\\jira\\projects\\WOOKIE'), ('https://github.com/apache/maven-scm', 'http:\\issues.apache.org\\jira\\projects\\SCM'), ('https://github.com/apache/commons-jci', 'http:\\issues.apache.org\\jira\\projects\\JCI'), ('https://github.com/apache/commons-jcs', 'http:\\issues.apache.org\\jira\\projects\\JCS'), ('https://github.com/apache/flume', 'http:\\issues.apache.org\\jira\\projects\\FLUME'), ('https://github.com/apache/nuvem', 'http:\\issues.apache.org\\jira\\projects\\NUVEM'), ('https://github.com/apache/dubbo', 'http:\\issues.apache.org\\jira\\projects\\DUBBO'), ('https://github.com/apache/oozie', 'http:\\issues.apache.org\\jira\\projects\\OOZIE'), ('https://github.com/apache/jackrabbit-filevault', 'http:\\issues.apache.org\\jira\\projects\\JCRVLT'), ('https://github.com/apache/ctakes', 'http:\\issues.apache.org\\jira\\projects\\CTAKES'), ('https://github.com/apache/clerezza', 'http:\\issues.apache.org\\jira\\projects\\CLEREZZA'), ('https://github.com/apache/streams', 'http:\\issues.apache.org\\jira\\projects\\STREAMS'), ('https://github.com/apache/commons-cli', 'http:\\issues.apache.org\\jira\\projects\\CLI'), ('https://github.com/apache/commons-math', 'http:\\issues.apache.org\\jira\\projects\\MATH'), ('https://github.com/apache/myfaces', 'http:\\issues.apache.org\\jira\\projects\\MYFACES'), ('https://github.com/apache/jspwiki', 'http:\\issues.apache.org\\jira\\projects\\JSPWIKI'), ('https://github.com/apache/servicemix-components', 'http:\\issues.apache.org\\jira\\projects\\SMXCOMP'), ('https://github.com/apache/camel', 'http:\\issues.apache.org\\jira\\projects\\CAMEL'), ('https://github.com/apache/james-hupa', 'http:\\issues.apache.org\\jira\\projects\\HUPA'), ('https://github.com/apache/commons-vfs', 'http:\\issues.apache.org\\jira\\projects\\VFS'), ('https://github.com/apache/hadoop-hdfs', 'http:\\issues.apache.org\\jira\\projects\\HDFS'), ('https://github.com/apache/maven-scm-publish-plugin', 'http:\\issues.apache.org\\jira\\projects\\MSCMPUB'), ('https://github.com/apache/geronimo-devtools', 'http:\\issues.apache.org\\jira\\projects\\GERONIMODEVTOOLS'), ('https://github.com/apache/knox', 'http:\\issues.apache.org\\jira\\projects\\KNOX'), ('https://github.com/apache/maven', 'http:\\issues.apache.org\\jira\\projects\\MNG'), ('https://github.com/apache/commons-scxml', 'http:\\issues.apache.org\\jira\\projects\\SCXML'), ('https://github.com/apache/james-postage', 'http:\\issues.apache.org\\jira\\projects\\POSTAGE'), ('https://github.com/apache/jackrabbit-ocm', 'http:\\issues.apache.org\\jira\\projects\\OCM'), ('https://github.com/apache/commons-exec', 'http:\\issues.apache.org\\jira\\projects\\EXEC'), ('https://github.com/apache/commons-bcel', 'http:\\issues.apache.org\\jira\\projects\\BCEL')]


def run_process(cmd_args):
    print "Running", cmd_args
    proc = Popen(cmd_args)
    proc.communicate()


def execute_inputs():
    p = Pool(int(10))
    cmds = []
    for i in inputs:
        cmds.append([sys.executable, "Main.py"] + list(i))
    p.map(run_process, cmds)


if __name__ == '__main__':
    execute_inputs()