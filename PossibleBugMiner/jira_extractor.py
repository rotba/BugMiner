import logging
import os
import re
from urlparse import urlparse

import settings
from candidate import Candidate
from commit_analyzer import IsBugCommitAnalyzer
from extractor import Extractor
from jira import JIRA
from jira import exceptions as jira_exceptions


class JiraExtractor(Extractor):
	MAX_ISSUES_TO_RETRIEVE = 1000
	WEAK_ISSUE_COMMIT_BINDING = False

	# def __init__(self, repo_dir, branch_inspected, jira_url, issue_key=None, query = None, use_cash = False):
	def __init__(self, repo_dir, branch_inspected, jira_url, issue_key=None, query=None, commit=None):
		super(JiraExtractor, self).__init__(repo_dir, branch_inspected)
		self.jira_url = urlparse(jira_url)
		self.jira_proj_name = os.path.basename(self.jira_url.path)
		self.issue_key = issue_key
		self.commit = commit
		self.query = query if query != None else self.generate_jql_find_bugs()
		self.jira = JIRA(options={'server': 'https://issues.apache.org/jira'})
		self.java_commits = self.get_java_commits()
		self.issues_d = self.get_data()

	def get_data(self):
		# comms = map(lambda x: self.repo.commit(x), ["d7dabee5ce14240f3c5ba2f6147c963d03604dd3", "033a07cf008dfaf63c2d4bb76bebf184f8b7a338", "d3e678bf2c00961a33854ad3a0ecb0df7dd23b08", "d4bb41f7968cb40d39f66b2c0430dde3eef2e618", "54aa413c1fc4b02b1bcd90228e10bb2e91b30876", "838fe5fc64d02bbab15e71131aca84a233558755", "b12c01d9b56053554cec501aab0530f7f4352daf", "fa6bb7e3c92145d29cd97820718ece69fd6ffd62", "d795c5fe92f6a2de1811515ec7851485a2840c74", "048252939fddb381856c41f94ef1ce3f84057b3d", "acf76a64d81eb9c901d92fe718c0f0ffb4d14ced", "68628ea2173da55de9d767d17fd61558d4b140f7", "836c4b953552c4dd4359d45197b0f241824ba32c", "c22581fb98ef95a52d360b9ac84fde547e9883c2", "c6d2f094af965cd6dfab8a668946c60aaf616ea2", "e43a19e433b6085b91bf44f534dbf055db313026", "aefe614e7c4846b173e102e1e99af03dc9d35e01", "235e80743cc75d3812c1fa59deb35df4a4c2af6e", "717833ad539511dc9c48eb488ce88c4337b05651", "e77e233f0e74edc6271a5dad2c8b1a7fe22925e2", "dd352d27c1b955103b2be76f2d5bca88f3b8e48b", "2699cf47e222d61b5c4f5ab0757c63199e3fd62a", "3864f42f1025c023d8103db4c984c6ff723d4292", "ce6ac916c9fca1ff6362dd99c380256ac180caab", "f6f9d4fe18590bfd8b03e5e87b75af9a18ee059e", "411d5d8a30873e82c4dddc1497b944ec862533e9", "d016d322caa1e0928012287840bf40bf11293480", "958c208009e3e1828f3b3b6c5a4598ce8f053313", "7a6089c0fd2f52119b5519ac30907875186e8815", "84587e3bd3333f0424e78e58982240e16afa0fe6", "0c8e965c9369ff6263bf9b27285d49c296b07387", "655afb51b95e4bff1c4b86d40023da112544cad2", "27e6e47d03c13d3bf53f759426f0b3e9c3aaff58", "62697affaf3fb93c5f667f76fe54deb78003ef4e", "8c130bad35f52ddfa7df2252243d86168d29a41e", "12ec68e67fecb7008f0fa2dab9c1679cdccf6cf5", "60c9b0e05868fb786180b3d7403537b2e66dce03", "035d8d3dad64179c6eda295233f064d0e0310f1b", "f49c4bdbe322506c6ddbf301cf842ac14eac3d67", "6ef60c2efd0c2607c400ac8b9e66d605a4ea2267", "4abeb2d772fc33aebdcc06ca0dfadfb660055cc0", "d34e55056c344bcc561e4213058f1d4fd8b87139", "23e3bae9d9d6ecfe035939e179e1dd3fd69a1539", "fd0470f664576fdfffe2cafd3f90f924021df38b", "368e6fafc5bce2abd9efeba0800d098a876cbcfc", "6be2c4ab2f32e036b7e48539087c07b104ee71ea", "f04edc5024a25ce5ce6d178fd8027b62ecc58b40", "74947b6cf59fafedef133bebee40d442b4559972", "5099b33a3552b1dbcb2b046057910f6d8edf3ab6", "0486ffb7be6bb98ba1a6d9737865789e09f9e175", "3d8a58aa28f15e17c21158d096e24b1f65e750cf", "15c83430df273aae65170d25ed95f4df62858de2", "ace49289168ed9367a6ed48a59f37719a9a544b9", "00ae4b3c4ef6503086aac939ff023dc57c85137f", "a09f5af5dd6e5b81bf7d3393851cc65f4855c619", "4307560767072216358f604fb9147f947c7dac85", "296e279858af9112d5500cc9a828a2d87d3218f5", "0297f443cdd0083445d3a37ca35d8ca87a5ec1e9", "29ab691396ca430688876217a12ed039b5409a07", "9c7c2c26deca3e473faedddff667249c11635d80", "cacb6b8cddecd296f2923b90b8955e35588a909c", "a68d61cc30e6508264365b7838ef34a92acbdfec", "43bb4c6322386125e58aa9276e68764b9389190e", "c9dfb89f029fe349a6057bec88d838b0200b9337", "6c6c17dc1ad9fefa5f795410cce937af56b4558f", "1cc319fa07f06043d7a39f64cca478e4441899dc", "a463b9fd2ac3046b7e669b3549385f962a2482f5", "26293c081dec22ba22f232f6d3d73c66a81e2ee9", "29c9a2728a08f37ab270a6a6c2a679a7228758bb", "03be219a6d7646d07c56b1cc98899d139cb62727", "39469baa4c0a991b171dd71b36f65c205058e462", "99c2dd5ea17081585bf559962e33366c4b2428d1", "e2049a1c4bf3cbdee365d0ed77ed5ebd6f802907", "945871993c88dba87c6311f01e65bb1a61db12df", "ac74696e322fa93bdbec982f55226f717be66d24", "b4405b7be7210fb3a0d08bff33a274c229744ea3", "61d64d2d6525caaef14d0e4f96c33c77f18512ff", "16db6681ebfcbb622255f81f5006020af07c2d1e", "5df8f87c4c865942a0c0990bc2c00a6d2ad0320d", "ebe7995a870c96ad5a7c9b05ed24bdb940bd166a", "7ed838caf2579be3c2d450cad8b61a10cf36ef0e", "2f0fa3b65a48bc4042491324cc546f9c32536c20", "4d89ea2c6349fe07b5dfc1134fa5cd4960a33710", "11970650568d41bd2318d3513c011240b7be3ecf", "57cfc63946ebd79a3732d99955915f5e12fa75ea", "3caba576686bcd6fe9e4501cd13e589a81032e2e", "1cad9b3fc6100a3b0f4a73b5ffac2dd23c680a48", "e64cad2d708e33347c8fa4a8b14a45554dd6b64a", "090001dbcf35c5729167fec0947cff0988f08cfa", "c9d44dbdd1cf61f17ed07d0df36af95d9ca51d0a", "dd6330f7dfa0f836918306ee718e48f9c4418dbe", "9f10da2479473d7a16e333d727771376af5851df", "9a049b4cd60afdfa1eb37d58485758f8125b5340", "5451e28bc4506703205741b2163d785aa4e27826", "6f48f57a6a0f21e6589a1d512a25574425dcc4cb", "bbd3cd3e96c1c09bba0e6e8b3974cb67cff251cb", "8a5f28845f28f5a5e2debdfc0fa3f89c738cd2fe", "cca6e63be096b1f1225ff7dea5336ee2048cb41b", "9d31098ffa9f9779a28a7cee1b471c71f67b4266", "a918dd64f4b96c362cf3648ebc9fbb6ec4eeca60", "648b5bf9544ea72be5a9597802a17fc5acb44e1f", "6f758f813c435105ebe289478fd01addd227c38b", "b471e61c790dcd9f6ad6be77f46f2e07afc56947", "b2b3685e8a3b9cddde06fe77bf7c3d1ed9ba4899", "cd4dff4df0699bcaebf4fc7f3e59ef77b9a9ba47", "b12228176d847064d8b48a6af82b9bb47b3d6740", "29972fd0e4cfcb772ae465b26b50230313f9c8a4", "b7ada46ce72027b5a5c5a0bd455aaaff38144b51", "09c6122d4cb05da6a3e9d4b0eaaf3d5ecfc33d61", "7d89a5e455686a945f2e3302f0d201e5e6c4a985", "3c3e6d1fa65db1b5d8c01bb42a5da85bbde67bcc", "31ce68f698019a9051011faa6bbb47b082ed210a", "97549f630d1971525d9b34f9af8b85e57212e500", "aea844ec10793bb440b0b1121cf7dba42bc13b16", "ed34e70f0ba7fc01769bed8dbf7f65a1a9058ec0", "3cebb673fef211cfbde44f2dfdda47bb20f98ee2", "e347b9887b6f02c00082c393b5a80d2126539995", "163d93c4e1e78a27b5dcd9502c2a4757fbd53b7d", "52664ffad6df20f8c864f3f22ca5ca22759fddc9", "d4a401460f56870c5085d87ec4f4856b6e6aacf3", "ed7a1d1bda0d981359261c20e8617a73d7dc482b", "31345be7c8cd6e347d0f7aeab12d99ed44187145", "c730e0ddfd1568e268d9dc45132108c8226855e1", "a1c050381e3cd2fff0ee9144f2d867d0491a1cdc", "486281b69d4d0f83ec4c35b85514b18b90a17eb8", "fed8c465cd4b6b6fd4158b284b317806064f0a33", "4f6a589842f4648f23a0d9e4bac5283893cac9da", "98eb0b0ec46c8a826a8a76a52636d8cc617d3201", "d32c1d879287b4b9ed81f1cd3b6b52025683f5f1", "31452f9fdf15ef93f05cacf2a4f0bad530b89714", "05acb51341cf2fd112ecbc8da517a33141b3a434", "453ae26882aa74faf4121b0713fd8d815e8804b7", "c496ffa3a53dab8d8992b75e27b7475fb6e407f3", "0abbfee21acacabadd74211921ed7c047201f68a", "9fbce438928982a43fa2ffac51d8550d39a47bef", "6fd7bb8c982a554b4f4260d77578773a8d51bf89", "a157a6f025c4b5eda63881124919b4271f85ba0b", "d60651e489947e4a57eac775928e4b82d77fbd6d", "cd45bd25057d9718afac37c69e6b4ab5b1b91a7b", "edd122dde40de1eb77e8da15039a3aaf6792610e", "8e58142f50588e11c75529c0489a04d9cb167e1e", "683ac820ebcdbfdc9cd1b4c8b0fe33fafdd93ee3", "00afd536d98a496ae88c523a9e0d511e6b765538", "b6f45ba65a19f05aebded8444e0de3aab35dc175", "05f333cec46f9e48312de6bde67722bc4cf5b41c", "ff74808a0f61614f075a38de8e0a5220f5837c2b", "dba5043a3beb6fc0ef732c6a7553d0f7071ea802", "bf42aac951f70ae6396055e341e2de6b55616a70", "46dce5b798874e3b1130ad3f39308d89068b8d52", "3e795106be703e44c0400c2617d340705748ef9e", "81336229e106373e3eaa190f61c8ac2667c85fe9", "b65fad1d762bdc691258a4b5d473671e1162801f", "ca6b5ca5614867a682b966fdfa35a6f7b48c1591", "a0d5a4f7fb1f0eb938f9b5d9c894f0337cfeecc5", "88a018918d054ca07551035fdfb14ef4475dede2", "e15598f83c404abb840bfe5cf285a436d2c3df3f", "ba5671c3f668decc79809d6ed8c8880219ab0ddc", "d7601cc4516c3e2e9d00e882ba3bbf9c8f16ef8d", "2c5efd4a5bc0fab0d06677ae6f406dadc76c601e", "2bf987b00c7d0b4d772b3502842ac3bb673198e6", "1bbaa907a3d0fa8f8a21795f00fc46b1e7e7c469", "2129a0f906deee6fb05563da91d8642a72ac824b", "4fca14426d641bb81e49ba5ec5c9534dc8375e43", "8b87a3848fc28ffaf536c5d3e5954239959cac2f", "3ab6160ca74fd1d6bb2e5de3ddb43d48b4ebef9b", "b6d67d32c1e43de488673d1925e0b6319588e4f9", "c80eee31e10872648a1d23fefc8e13bb3b0e65a4", "7aeed0b52f5fbd5a1955270046220350d9a72885", "7dc399b99823bbbd77ab6e6ab0b9cc1870210c0c", "329ebc5b5f3d7813fc50e58c9679db1b35e69f4f", "03752ab3ea833c939929b677ae6f5465a872f7be", "a5df8777ca65f6f40545d0c02455b2443c6955c0", "0a7b8ce9f466dd895316084dcdd1ccc5401629a4", "9c9d6f85aa15ab2e65d103b0b0d34769dbfe100c", "406cca3479f95de7543c59d8bd31856409b701b3", "c2f7fe03d7bbaf0ce42f9c0ea08c0871f39a9c24", "c77287289407b971e8e1811fd1e976e6f59093ad", "1fcb10afd65a0a007beb631a3ac5f1f6b8027d35", "ac4b6ef8f4bc4cdf93d062c0a55a0e43007cfef1", "ee817f06c81bcb356d3dee84cb9aff05376173be", "907880f1c3f86e55fd83eae3209a5b238e580a06", "77c7847b54d396de91f281f4c58ff69d67ee9910", "77ebfcd04dfb16f9f856dbcf6fe9098217c779c3", "fcde81cfbf6f7d4a7ba4e148471f1ce622d59f92", "5119a98a67b6b30fa93614ebe8df0ef950df357e", "3e0191d232a8574083f3648f2b6b8590ac132c15", "ddceb68bdabc6fb732ecf2182dcb589237277a58", "87fd9affb574d62ed26d669adaa3d7cf37e124fb", "8ef4561642c3b0b4173480b82708e192ac06d2a3", "469aa10c4736a905e343fe77e64fa9c7bec843b6", "5716665ac46861acb3b14fd56ed8b91d6ddc91f8", "6af91c661f3dbebcb599b67635fe858a26576ee0", "02ec12f6b89d247905e63df050349c80ba70735d", "49a9c4ffeebd479501cba457d5215dc9ec12991b", "49692dead827eac2b7a0f9c6b6e48f97eabd5dae", "2942530968d8b5a990b369eb619a7bf371c14c5c", "bc8f90a5d1fd8286f04fa7088c324db96e8cb36f", "2608c791c41fb82a55fbf8718e748b4d587032c5", "cf8cb44b4e4e8de21b65d05f8c73fa8b0e6af477", "5c22595f655362f983e73aca4fb79149f37a17ec", "ca890e427a1623b0e100ebe45a49edaacf17db39", "ad30687ead0422e4e71af4d7632f920af5b678fa", "24ef1035df8f53a1750884e8cff91d277528e6a9", "332e4986fc077212784ada8d5f3048473ccd06b4", "b16c8987e6910aeff242ce364753e6eec5eafafa", "8efad87c5e2933953eb7c254110e04f91104044d", "e7b51f0ea9a76e351fef07c806dce00ff47a2888", "0c52b66e9dd568cd9af1529cd1b0fa0819c53e9d", "4b51beae8e08e82458792a63dd867319cb40e1e4", "4885ea7e2eb8a557879a08be9eae85224b718063", "4fdc2b7247a033defed10874eecb986778ad451c", "4c5599b6694a31e8ce84a1a0d88100827d98490e", "9c9763a5ac67683553f155a33338bdf98e1a6937", "ddf56cee81e96faaab73d5d2ae70262692431fc5", "6bd95ee7eec85356b90d407084c4e45eec97e8df", "6bc0e0554fff5cb287caa56a10eecea60bf840bf", "3e832b08f0b7b2f528af65bd2c10b414e21ded07", "8ef85fce930576a40daa400cc1419da4debcb654", "33595666efff7b475e461af98446e682a5724ca5", "9d5cf328f700e655a38cdf547fc86a273b854b78", "04d1fb7cc895e054941280e991ef129cde11ab8b", "b4bfb99c580cf647b4c7691ecd91cb80f44d55f5", "9d73a101d5bd8f9ba3ba12f842862e2a72f14019", "03e6113c9ea555bf93b9ce064a2c0d1cd8073cc5", "ea21418703d689ad0fa926ca49a941076b5ac43a", "ec9d7d201f0fb580a32b599a6340a220063ca82c", "af7df6bfaedc6b097a91eda6c789e5ee576401f6", "20ab62de27c7e34d1c09b3cd0a14c0e32e59994b", "51a7c9ccacde4f0a40d3f3a0a0c7b2d270d22684", "a682c4c961d6940adedc55b57f40235bcc8f59d6", "acbefdf903b19385d7557cf6c41380afe81b5eed", "fdb902bcea910756c9f498b0db9bf3a1870cb2f2", "aa944e848894e16adec24eeffe29e11b96ad29a8", "eb73a4be05f53e33679146810c28e74224f8b359", "94356cb82bdefc805b8d09bd00057ed8e260199e", "1e785151730deb210bbd72f96c8f3a599a24382e", "39a63cad3ad912f412f75a2dcdca400ab8e37ab6", "ab1aea62e8c1a20652c004c55bffea83b8f7eb60", "fb8a540025c7ca5a3947a27e74372fc904fb62ba", "dc2b9a1fad73867e1499fbf03695eec051c536f7", "3083e916b9a58aabca69a4cb7462415d4a7468e4", "9769f860a20af595c85ba751c4b6652a8690a2e6", "609cfe70bd396dc311c694161a59c1ac7076735c", "84d1ee3915c676005fdf741b2f18d7917761465d", "da8cc2a822211064e5fda5188810bf16c48d1da1", "4e0b3e6cef33706b8e2eb510e4a1a04433b5938c", "c256022ce85a05be039e81f152fe895cb4f38b3a", "c3f99103fd06292556f9eb0034365f0389205434", "f52da719f16ad7379d5b7019ac766a80ab48d6db", "2c3dbde39c16161dafc4b5cc03db4e259bf7fb7f", "6ef64ddbeff4b23ee25e3d3f51f8a07c49d37c2b", "ad78ecd3a85fcfc61b22cb045b3881cc9c170b13", "2b39c7599a9930f8847f8839e9612ae5cdc56407", "f8e3364bfd7fa5d4d80c7b249894ebbe6a146b85", "f5021783895b9352cf428f7b7d6c8731aab34a20", "0f54339112fdc6c887d2f9e05d0826b1c7462873", "3bdf69a7d2e119aa722a097d81a99fd63d76be78", "554605b284b0c4ac32b8cdda512700d780915a8d", "b93fc6f1b3e16e8f76dadb4d7a94a782879fe3ef", "96c92f509db1f424147ac0f1b7a5cfcfe6211435", "7e2326a8050352a38c2d278174877211d1049436", "374538b413fffbc254dca221e7a56021421e8871", "b73dccb6bc47d33bdb6f1e51b723c7ef6bf3e1a3", "486d767688ce4c93c9e90ede0b27459cebfa5233", "eec596c1b44922b7bd1e177f485338f8e8adf826", "8630e56468e1d25920030251d9d97a862cc719f3", "3d6dbb3e6e567eac8191e408b3de47413301da94", "9227e9f3d5090be28e28639ab92732c5be0507cf", "8fd76a41b32b80353820d4a8bdaa08de5529f7ee", "48b28a6d31c3afb741ffa5ace4c0c4738101b539", "83a8a97e02d1ac479bbea6770732e4ea9d8fcf7f", "9e22f46f2403b89dbc8454cefb8b83881f437419", "a90b827bcbed21bb8a149cebdfdd483b3a20d7fe", "edb6775bf356eaaf656730589cc3340a15b602ea", "dd8480f92b6a7750cb65ce2eb95c9d2fe8b9b988", "bc075703823e7250a7ad7db93ef58712133920f2", "915be4f4fb999a79ea1f3f90b3a2637ea086ae26", "24bc3dc6f752d342a2d994da24545d4f9698ce90", "5498c0eeea7d2a5d6d314bcddc7d307830e97c27", "5c29442148711a86f01ded50bc5e13f1343090c9", "fbd2d6db793746fbb5f605731157b5181dd6ee9d", "a547dde812cce268518796e116f63ef0a3f4c8f3", "1f16bf8e5ef4848d9d2e91e1566c1cfb5617f311", "56237e39f39092ede166eb790f3d5c0b4644d8e0", "b11403daaddbbfd5385180a611b84ed5d131772e", "44d14a51ff1c93fc597aa85fc828507d214269d3", "e91ba0c53057f51623ede0a4c0440f7651444501", "e48876756c9b1042e27529e71756df079af70e12", "232cc5ddc7a1adb357959102accd52a3ee11d755", "c181ed933b85bdccb109cb231e12bc421c2d2e67", "27fbb0a2303433efb077ec449a591114c264e3c1", "5eb3dc1d76fe98ccdf522a0beb69f3d123ccfe98", "99ad6801379ee8e0918d51b7d4bba762694afbbf", "00a14bb29de9d26224720194d596604f90570480", "bf24bc0a11daa83ab707c1576a5605609b35d786", "8d38e36c861acdfbf6996c924f66e31bbfb01088", "8fd2a5298a5dbb2272279ea6b01087e9a96237ad", "527f3d72120f6be58735c437d1f6453029485b15", "4c58d09499bf164ed123410464d43c20b764b5d5", "914cafdbbe3748003cfc766c5d9b99339d08ce79", "23eb923e98ac1ee079834334d39a668f5bf231a3", "f28f04af7e60ffc04550030c0c99e8c7dd931442", "218352a1ce7de0881416eff741d832a1abc51f07", "a7e03539f9944f4847164b4bfa14b1f2db077331", "efdb4679cb28841da7ba9d8e755596602b630893", "c36e5a0461b66a7941156dd9ee502c73aa0ee28c", "dfcf3d4c7cee2dac641ea5b331965ad03ce37364", "c70b12f68245eb179de7653639ca14c6491007e6", "ffc3b3cc73f7f931ac82425d9a0803e1c672aba3", "dcbe0d27ed0575fab0f2176503e5a5bc1014dfe2", "4cdcefd5a87ed11e84ee4a016b989102bc84cdf1", "0ce025c5cf0ab44a87bc56835e34803827f74b97", "7d6167539dc165877b62ca1530144ff14931f532", "7b76a7ff27780dc866240d43dc0d5deef4846416", "4f920c7bc5fd262c2a83fe44a7fb7b7bcb2798b7", "3e7e7c95e68a8b3be8204e9c4120cc8199b5df57", "aa18a7989e73510ac148ef56a47d151385e3b268", "2697354c7e50b9b06c44441accd09f3cff594c6e", "9c0f4ca22c79a049b9459ce6f4dba8ba527da5d2", "a06209b1d5e263fd579afe66318560deeda7f66c", "fe76f5716d09471a8751ad5bb88a7650f73d235b", "4e09c6360355b73801b95c97e139619acbe012bd", "433f21c4805e7bb930964f87d15c30f62e0eb5d5", "55310ec7f4c8f2bfe6ff29485dfee156e6c9de84", "a64d33c78c143f401d2d7ef795872fcc35fb2200", "acdb2b0ea9082dad8120431ebbf34e68b76aafe2", "363ee3bf4604a36515df8deb49c520bc3a488184", "1d637c8e872ada489b3e928b854be0959ed0a0c4", "a2ddd8cffdb3c69d5e8fbfec24a939ab7c3f3bed", "7171855cd159df475f3eaa98177916616288db30", "355eba97dfd9ae2e61ca856f0c70e001b203a0c0", "a3f156bfa445f5c0172a90107c6c15402bfa120e", "963100eb1806048809b1fb2cb5076afdd640cdfa", "58b7c17d1833caffd5e8693d656a6efc02463c43", "a9f559d7a4921578cfbc827ae89f5dd0b80b7d79", "7cd31ee5aea3b05525b84b0bd9b83df043f44381", "e10c23b3ad00dd9d8fb059fdbfc40273b8e2469c", "9ec715349810ab8e2d149028679ba6baebeae14b", "e9206475e683c35b09810a857ddd7bdbfa8f60fb", "01c02e671a82fc89fca8748175a741a5c5605962", "771e368ba531ef5063b89811d98a3c756920f870", "15303fe8bcb1b975be727041c0094e471f0b801a", "7260050594e7a13283d2dbfd1a079149a63d43ac", "ab9f799ae4a3eec42e00a109ca3171cbdf7b6cd0", "71166dea776a676601d35bef3922717aa2d56301", "794595c85cffc6cc811c60b1d8ae6fd3a341bcb1", "2db38125fb23d9ddfdf64a0cf18dce677a74499c", "94ff74c029ab8ea6dfd121938b2e6a6bc414a8b3", "5dd29c4fd97c9a9de8d716e52e4998db1e92176d", "8d794b56dc413f41f0cb0a288aa55b55a7f198e9", "9385906e6a5adad9f820aca6e8138dce41ab122b", "5ffe387253086d52017d32f7d5b20cbd912d56a5", "c46f54556357b08dc0d092cab3d316a1205b7d51", "2936d550002fe564beb99e56eb6b4c5a7d33d36a", "c4581fb85824ad27725e17aeb49bfbe12ebea40a", "ba80052ad7c7992a15aae7445488bed7584187f7", "9d81bddc52fc3eb851f52099263d28b18bacde69", "14aa5bfbab763cb00677d89b7e6cc0077c8a6ca7", "970bafe849a6aa2e4e5ed1140e033fdb9c8abe32", "ec32a29d3109df74e56b7878809aa0c5be862666", "c7d7f66f8c9e389d8654a6a57f0e14040f2e9d51", "066f587584998f82e738496cd2906de8ffecb9b4", "22fc879bf987c2ab1fa24d68c10a97cb4797614e", "a852c4f55cc320087d4cfa300fca5ffb9c759918", "3dec31215d95917e7f6f5113ce966d2d61231800", "1e8e3c86d433337100aabfd9e22ce4cb2998ea9f", "841c587bcd64a75a8badf51eddb62d10360ba69d", "c183694b20f785371539284a3d6f84d29dceea68", "38b15098fb9313a837e796c703eac90dde179f98", "6a398bd3f6245543091fd7c0e9e4facb34a26882", "ceccd0b65b0a24bf44f4566a94c901c7c40135f6", "556ee2ad852fde5c45ee481809df30862977aa65", "6f7177ff791539fd277e7dc59e0f7fbe5e3f0e5a", "ed77de42dbeb0b1fb5f7fafd42b02b7f43805929", "359aae57ce045de191a14bb369e7980154deffc6", "3b1d2498e25d51817c47e470a66c9251210b9dfd", "7b7ad9596116b402a938d5ded50a2ef621677c03", "33280e0e96a3a6000e3bb747667ffca002752595", "7d3194a3be19dc81a425ad4247b85dc7891b8660", "1ca0efd92bf7068fb1ff0366dfe0f55612d56068", "2aaec12dbd492d716aab53f7ee32bdb247404c35", "f033bcf5dff844fc01baf480596582b89095435e", "04be3280412570d8923594b6f3df42741f098008", "6b7db9975871d6a9426fcff284661b33ed079448", "0e3c51ea1dd800ecf70f43ebdeb9559c07b72aca", "a360ec5add94fad571114f6090e363df6c9295e7", "8e0c444b1f1bf61215a298c2b782b5cb451f9cde", "cb6c9b845c0a883ff35a30fb0018cccfe4deb024", "3cfe5ad70d02b22c8464b6073de9fe55830964ac", "80efc84b675c8defa5e86b01b85e1dabc84d32f5", "beff3947978d4573e35a40a7b0ad8fb7ec89a2f6", "aacc74d026ce20cf50b4e7de0b7b8032ab287f7c", "02afb8bdcc0fd496f9382c999916731e0454ddc2", "02b5424694e1eb2a880bb807e8e5556e523e73d0", "3a9afb5d5dae8b5e4db84679ec39738d41d8fd75", "a570bfb2f3c4e7cd99f25d2ba9f39794f2a492b1", "a0ffec146e84fdcf4c747b4375f92ae283944f4c", "0b57b5c2d885b9223c0c77133844a3fc39f5bcc4", "f689fa7ee25c0c9c4bd4d68aa51941eb558f7026", "c2da98e37eaff64a0b12a253b7406385cd80b253", "b97ef3208fe5848c96c86d6d7b6a6bfb962e0568", "d0ced9671ef45210a1d0545f32281f3bd7724862", "a13fdace85d18eccc4ec9ee918e86541204374b1", "375fde60b42c44b57c6931894ddee177b063fbae", "6a306fbbe256c267cd1c5a863c78707f4c43085f", "a9a5c03c4581fc43e0e17372dc4c4863e280e762", "11787f5fac99e14261dbe792e75549ef8fc19e42", "d600793f89bc2f03dfd9d258b9eb3942985fcc7a", "4a75eefea9d04499c7cd4c9e99c9df3e4b73a97b", "2335991f60135e641413a464687f75c15b82b21c", "15521f132f69f80a42496a5fc38a49caa27c09cc", "3b004508773ee65ff2de9e90e12d8926b1a52489", "95051f2a352f3e7ee83acf203d75b803a26c3f4f", "f1d00dbf40f16ce8669628951b813d7972c07c45", "65aea2b06b33c6b53999b6c52e017c38bf2af0b4", "eb9495e194c90d18ed5c48eb53f8ccab664e5e71", "7e6448348853234fe76c732ffeccb76200fe464c", "9688c77128e5c3d53c1eeb4e72db62ff10dfafda", "79db92bece9695d5841626dcd94579a6ec84b70c", "1bafbb815913089847ed8689e47b958c44fd92c3", "cc922f459b20e997c2545bb1902aef6123eedea5", "a9406a5e17991af17b42e3cfee97d2060ddcb520", "0365ed2e430f3513931c01994e75fa55d1fb1b01", "fc87e4aa6f50760ad603b2e69a766ece2798b8e4", "c20630790bfaaaa08626456a1ff8dc56b073aaad", "cf55425220f3c0dcab2fe6318e19560bf4c7827b", "eb7202d524dbf45d2d0e21b473e73e5401ed10b9", "ff8e253c1ce8d3ccfe35b0c12fdc72937dba5af8", "e8fac5b3060b8af39ff787fbf8038980b999c611", "4f421985cb2d1c75b8c2474719ab2d5e38d2793e", "ace2ad96b75fecffa2c54d220afe6c4f2b0d36c4", "192c0d0c9aafdf660e0b311b7fc2da11ecb9d572", "0a176a5aad749a0b15559b705b906937760d4a77", "5cf7785cf2540cc8cdfd7d21b4f8bf540fbdc55f", "895ebb79404e3113766a0ec4b12c3a100294a96b", "5f6845257016bfbaef26e998edd8f660c5711ac1", "7dc73cee673ffde25441b1adba6d467873ed134c", "1233a93d97e9fb7f566b0b4f52d3733659f0ac7b", "746de4d60f1ea1e847dbd9fc1b940c53b874d787", "1cc2725cecf73a1156af53d21801a9196154f389", "65977bba2a5900c43dbb9f4c8512daf38b9163b5", "bb78082b0028b57a5bf1ae30858dda6aebeacf63", "69852e4cb55d34e6513e0b66af7d75cb1b1408ba", "e2293d302bc5f447563c5c6c93907b55bba6e91b", "eacb983cb6155dc00e98f5ad4c9d71244b7dba83", "0aa8bca3ede9bec545b7228733df67905b7e8663", "74c231a575c9ac307b617c2c322d0f4151baeb64", "9005c6760366b29eac19e307f943dfe6f1e522c8", "d1e8d7176952d7e82e2d72ae08b2ee40df17902e", "f3df5ae5a98c31220a5946b70daa3fc2fd3752b2", "f5ad49dc58e0309b88084f6dda2d73fea3612804", "2e60efbfc81132cb46e5d6edd2e0dde28881aadf", "4533e06da0231f88cf8a5d1b6a3708841e3c6880", "990c0c2096fdabec508371cbf96f9e77bd61f12d", "61671f5d97d97e6f379dd94391ed8449f8c15073", "7d231d03247b9171dcce6e1758deb5c49560a6a1", "43086f4d2c69d69b10b52507be21c33a3397569b", "6194e6854392740a157cce3bb252af10244af8af", "70dbd04eb37b246d97ef3a6854f07495147463a1", "892f3a8b1e44efdf86ec9aed0887de7afcbf01ea", "e12bb7a68d1e1cf60bacdbd2e68afe6b0b6863a8", "8fc3a0925db66e3a15d7ad5f790f0201ed73b214", "8494d9310defb3bebbbc2d9f46393840f292a5e1", "f54cb9e354b71e720602acfa0b4da8f100b400c2", "4aab1c1777a314644507d2acf27c814390f685d9", "7175b9027fb4c8566822c57b428363bc35893d74", "de00e27abdba193cace29950dd75edb2f44cd766", "90bc595d756376cc40ca17ec13cdbae5fb023a90", "671b314b1c25c3d4b390a61ef6c0d7d03b062806", "1e33ed3bc35997cd4c8bcad689cd460313ea5605", "f2c263dd409f62c6c3520e48816c9fca9244e854", "3e9db56e11340c06c39e71df4d320033eda5810c", "9f255bc73011de43ef115e11c3fdf5438394bc42", "3210d79b0330614e8088f31dfaa3712df027d521", "a54b37a407abbf72e9ac8f5867f873736757e1bf", "d3c776ce35940cfb5f4b8127d239e580860a5bbd", "a85081207afc8d5bc7c9a9e9c09ad72b3c6743c2", "90ff7e32c5845138ef469cd06212545bfd0d789d", "88f140f5cfd63202a48bab7a43e2c6cae05ea8da", "309752746d8ab0d8fc713c4f0ffb766c4135a07e", "9413f4547eebadff017226c66b4cf87376433075", "cc326059cd05b9df51bbc82fba6528cb09f4395e", "209b64873106f14c745a729baac6b5d137ced64e", "b93a7d267f8d1899354c5e2b8c1c56651e50d99c", "5cdc797a9fe12f46423feb2588e94d5e5358b56a", "80a1126072d9af786e09f30a4fd951b45c844cec", "1a3749fa632fdb8ad0bcb2cea673113031f9b4be", "444dadd5eb090f6e2998507e444b2014905cb90f", "761273f9e69c4a7595e50ccd6a2d9304c398d0b1", "2764fb8606964c3350c781ecf5df4042706b4099", "6029c0d5c4e07ff217fcd43a6c1e81170acf603e", "1ecb5f93b3af6ab23cbf2eaa329fca7ae140f530", "9a8798b8e19b2149e1f5b678804f328dd0be6686", "320b2890038dfcb9191ba856c0e84e368851d24e", "58a757e0f7295af14bb8051a42d75bb0ccc8cfe6", "98672cdd92b6325ff78c763955a7c045b364095b", "abd6b8744917816a4695aca42e9f8e9cf9f09263", "cd129b5741d96d169823daadf6f40038ce773041", "38697cbec28a90ed7b4726b081a82ecf98cd47fd", "3f784c6708e594956a5a62d9f421eec99a4b5f4a", "98b088d6f1cdd44aacabc60346b8b065ae2eb94e", "24b8c2a918ac599b5aff1265f2e08014de1a2fe0", "e7a3a49561cc1f9ffa4cd34307005f559dcefe19", "5d50c2e9391a9f31ea435724aef9e0bb73624984", "191c03d14e33606ffd4bef2972704398abce289b", "e607d65bc58087116408988342331dcb20ff9bba", "5a7027a1d2a82895b49d4131ef20f3e59e417712", "f43de5a24b56cdd6a3c5abc3e5a38e2410089d69", "1f28f464e91300cfd50f881ac37fd6d467d5dc7a", "9653e77d935bb00b7a38be483991e8e185f751ff", "18aa69a16f09232413e06d04e921427ff4356cec", "02bcf2097e14a70274abbc1f9703548b82458f41", "c2895d525a941e22dff4e8a757d4025ce8f6e719", "f682eeec632bcfba9c879de077a968b926c3fc31", "a147d7c0b5808f7e8732898e907274abedb8c486", "1760249f26536047e54e3932f47910217a6c81f5", "3574c9c68d8620db9b89e294daa34267f2a09712", "3e7e335b29e175e1d937a7b4a0f70f0f1fda0d94", "fe841bc8760027eae3f9d0105238780815451346", "16290d86c3a976f7c323b0be6750ad07f4840018", "2ec36ff4b817d1378b75f0654648a260c3d5928f", "72d76f884e3997ecee322e8327f51053d0a34bad", "443ecd352deae04f650b2e3dddb534bb19734806", "1e0159b733dc7a8f48ce8943e1f15046c791349a", "13d772ab6317c6151b4b4e6111b80af2bd30cd7b", "1882defb38ed244d667114399ea31e6b938c31b3", "3b7922db1a2e72181e1a00168d2aee33bfe1d4a3", "0bd05cec54c581c971d90380304aaa23c9543296", "0c030081bba17e607f8c79a0b95f72935be93efd", "e105088729ef12acbda1fe4e71f462f84d98f981", "bf2d405437d5807525406e26025e12d445e00b20", "a1243c7abcb7068c944d3f8699d8eb08c75228a9", "73aaa1bcee194e8fa73cb0c3cd60ae2eb3205bf9", "7a4301ed3ac21f73b049d4111f46ba6cda69145c", "5e170d4373c28a4b520196591c4d94ab8073bfbf", "a30b143e41857be010149e01c5fb0df363157e6b", "63bb15467fcd6e8766b0361e78231f6f7f6a4a08", "5a74addc0ded0120949fc330564986607f6d8b39", "4f22b085b1569d66d711b79751478dfb8448c353", "b2821d921ac4cfd3be468e8bea9123f5cb627cbf", "1c5e96cf617b231ce8d902fc86eca84edb9cafe7", "46d5775cd42e8c6c378f2100c70aca18c3f37df4", "b6d23c189e852fa2e41b441c18bfe3e66e3f67c4", "7842600560e02a4fd213d175301b4397bbe030a3", "dab10395ab59a36be52529d3afa7ed370ce60eef", "64b7ded37f981e298fcb62a996cbaf4ccabb2a96", "89881ce207444a9d53f041bf9a14b5b7d623dca6", "09cc658a30ae194323f1e444be73d396544efc6b", "fc4f13ddebf2b9519d75a3079adb307313e79259", "9024f12e0fbef206330b6317a537354fafbe9cd7", "6ad18f44cdfef5e80b343d9c06787b850fcfc9fd", "a20c46cc71e7a83a5c5cb4256f5c6a753b901a90", "40f8ec95b1c1c2e1713d26e0780b3bd2f97c9bb1", "99aa587d171207c0c557ce65397f767d6a42cdfd", "3e14505381eefa603adabe61171c0c19fc685b2f", "9b5dc7fae4456b12b75ec21d050b9439e6527c47", "2031de70c117fdabf793008fe22dd9c97c82d2c9", "7ae760e29ad3ed5874f7f50c27c6f850ab1d8025", "a383567c2c947603c4c7aa12d3578d771bb58413", "7cc610e1b3f164fe9de00b1a35e60fd00a69bb46", "95b2cd127346486cece4cb1450f444fd9bd54337", "c0320f14194608d31b9ffaae9250f28c46017b75", "952fb54ed78a2fba07db4653cc674f5641211031", "71cb9363c07839e68712edde4626d53aa928cc2a", "bd9a9b911b4e0205c9dfd4527063e6e1c0fd0c44", "d698d49793bb96aee6a8bfcc4a174c922cb83cb8", "415381212291e843e9091f43f6db8c432eb02aa9", "85e53850026aadce49bc99c1ef2de9d5c7be0451", "27b9cf566da9772961b2fac3c2aa6cc1648ab2a5", "011f33807e7e794c2c06154774ec167b818930f2", "b67373f22bb84d9e40019836817784faaff61ec8", "621ded89fd909380ff5c3d2c5d13d73dd6e5b982", "cb7b84a48aa7f500c08733b06fc78e6c1f0bba14", "95c515db2f303db049c79a7bd0c260ec559186b1", "308d26fb297c6248f98d777b7a94192fc0ecfce2", "9b497d1fef2fe183b2099f1a835113dade8a0227", "0a4b0e80bad54e88c1f76cf8f37810757b1b34c9", "c33ac04618f97c06fe4508b5d41465b2c11ba1b9", "a194bc4ba2b771807e93e664245f24e3573a15df", "18f4e24451b1d835ab1897f49389788f78063a52", "7536ed91afd9a3fe744464e34f95f3108c6bd5a2", "feac58b6f74156086113bf08bbfe9feda1c14b79", "5af482ef6341369d6ba30df87ca2c8be9f0d0c0f", "15a92302501d5ee6a319442c8109eafe37ec4595"])
		# return {"-1": filter(lambda x: x in comms, self.get_java_commits())}
		if self.commit:
			return {"-1": [self.repo.commit(self.commit)]}
		issues = []
		if self.issue_key:
			issues = [self.issue_key]
		else:
			issues = JiraExtractor.get_jira_issues(self.jira_proj_name, 'https://issues.apache.org/jira')
		return self.commits_and_issues(issues)

	@staticmethod
	def get_jira_issues(project_name, url, bunch=100):
		jira_conn = JIRA(url)
		all_issues = []
		extracted_issues = 0
		query = "project={0}".format(project_name)
		while True:
			issues = jira_conn.search_issues(query, maxResults=bunch, startAt=extracted_issues)
			all_issues.extend(map(lambda issue: issue.key.strip(), issues))
			extracted_issues = extracted_issues + bunch
			if len(issues) < bunch:
				break
		# return map(lambda issue: issue.key.strip(), filter(lambda issue: issue.fields.issuetype.name.lower() == 'bug', all_issues))
		return all_issues

	def commits_and_issues(self, issues):
		def replace(chars_to_replace, replacement, s):
			temp_s = s
			for c in chars_to_replace:
				temp_s = temp_s.replace(c, replacement)
			return temp_s

		def get_bug_num_from_comit_text(commit_text, issues_ids):
			text = replace("[]?#,:(){}", "", commit_text.lower())
			text = replace("-_", " ", text)
			for word in text.split():
				if word.isdigit():
					if word in issues_ids:
						return word
			return "0"

		def clean_commit_message(commit_message):
			if "git-svn-id" in commit_message:
				return commit_message.split("git-svn-id")[0]
			return commit_message

		issues_d = {}
		issues_ids = map(lambda issue: issue.split("-")[1], issues)
		for git_commit in self.java_commits:
			if not self.has_parent(git_commit):
				logging.info('commit {0} has no parent '.format(git_commit.hexsha))
				continue
			commit_text = clean_commit_message(git_commit.summary)
			bug_id = get_bug_num_from_comit_text(commit_text, issues_ids)
			if bug_id != '0':
				issues_d.setdefault(bug_id, []).append(git_commit)
			elif any(map(lambda x: 'test' in x, self.java_commits[git_commit])) and any(map(lambda x: 'test' not in x, self.java_commits[git_commit])):
				# check if it change a test file and java
				if self.issue_key is None:
					issues_d.setdefault("-1", []).append(git_commit)
		return issues_d

	# Returns tupls of (issue,commit,tests) that may contain bugs
	def extract_possible_bugs(self, check_trace=False):
		for bug_issue, issue_commits in sorted(self.issues_d.items(), key=lambda x: int(x[0]), reverse=True):
			logging.info("extract_possible_bugs(): working on issue " + bug_issue)
			if len(issue_commits) == 0:
				logging.info('Couldn\'t find commits associated with ' + bug_issue)
				continue
			for commit in issue_commits:
				analyzer = IsBugCommitAnalyzer(commit=commit, parent=self.get_parent(commit), repo=self.repo, diffed_files=self.java_commits[commit])
				if analyzer.is_bug_commit(check_trace):
					yield Candidate(issue=bug_issue, fix_commit=analyzer.commit, tests=analyzer.get_test_paths(), diffed_components=analyzer.source_diffed_components)
				else:
					logging.info(
						'Didn\'t associate ' + bug_issue + ' and commit ' + commit.hexsha + ' with any test')

	# Returns the commits relevant to bug_issue
	def get_issue_commits(self, issue):
		return filter(
			lambda x: self.is_associated_to_commit(issue, x),
			self.get_all_commits()
		)

	# Returns true if the commit message contains the issue key exclusively
	def is_associated_to_commit(self, issue, commit):
		if settings.DEBUG:
			if commit.hexsha == 'af6fe141036d30bfd1613758b7a9fb413bf2bafc':
				return True
		if issue.key in commit.message:
			if JiraExtractor.WEAK_ISSUE_COMMIT_BINDING:
				if 'fix' in commit.message.lower():
					return True
			index_of_char_after_issue_key = commit.message.find(issue.key) + len(issue.key)
			if index_of_char_after_issue_key == len(commit.message):
				return True
			char_after_issue_key = commit.message[commit.message.find(issue.key) + len(issue.key)]
			return not char_after_issue_key.isdigit()
		elif re.search("This closes #{}".format(issue.key), commit.message):
			return True
		elif re.search("\[{}\]".format(issue.key), commit.message):
			return True
		else:
			return False

	def get_bug_issues(self):
		try:
			return self.jira.search_issues(self.query, maxResults=JiraExtractor.MAX_ISSUES_TO_RETRIEVE)
		except jira_exceptions.JIRAError as e:
			raise JiraErrorWrapper(msg=e.text, jira_error=e)

	def generate_jql_find_bugs(self):
		ans = 'project = {} ' \
		      'AND issuetype = Bug '.format(
			self.jira_proj_name)
		if self.issue_key != None:
			ans = 'issuekey = {} AND ' \
				      .format(self.issue_key) + ans
		return ans


class JiraExtractorException(Exception):
	def __init__(self, msg):
		self.msg = msg

	def __str__(self):
		return repr(self.msg)


class JiraErrorWrapper(JiraExtractorException):
	def __init__(self, msg, jira_error):
		super(JiraErrorWrapper, self).__init__(msg)
		self.jira_error = jira_error
