# Adapted from the Example.C in MissingETUtility/macros
# local imports
from . import log; log = log[__name__]
from .systematics import Systematics

# atlastools imports
from atlastools.utils import dR

# rootpy imports
from rootpy.tree.filtering import EventFilter

# ATLAS tools imports
from externaltools import MissingETUtility

# MissingETUtility
from ROOT import METUtility
from ROOT import METUtil
from ROOT import MissingETTags


class METRecalculation(EventFilter):

    def __init__(self,
                 year,
                 tree,
                 terms=None,
                 verbose=False,
                 very_verbose=False,
                 **kwargs):

        super(METRecalculation, self).__init__(**kwargs)

        self.terms = set([])
        self.year = year
        self.tree = tree
        self.verbose = verbose
        self.very_verbose = very_verbose

        # Initialise your METUtility object
        # https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/MissingETUtility
        self.tool = METUtility()

        # configure
        self.tool.configMissingET(
            year == 2012, # is 2012
            year == 2012) # is STVF

        # Turn on (off) the relevant MET terms
        # These are the terms required for MET_RefFinal(_BDTMedium)
        self.tool.defineMissingET(
            True,  # RefEle
            True,  # RefGamma
            True,  # RefTau
            True,  # RefJet
            True,  # RefMuon
            True,  # MuonTotal
            True,  # Soft
            )

        # The threshold below which jets enter the SoftJets term (JES is not applied)
        #self.tool.setSoftJetCut(20e3)

        # Whether to use MUID muons (otherwise STACO).
        self.tool.setIsMuid(False)

        # Whether METUtility should scream at you over every little thing
        self.tool.setVerbosity(self.very_verbose)

    def get_met(self):

        util = self.tool
        if self.year == 2011:
            if Systematics.MET_SCALESOFTTERMS_UP in self.terms:
                return util.getMissingET(METUtil.RefFinal, METUtil.ScaleSoftTermsUp)
            elif Systematics.MET_SCALESOFTTERMS_DOWN in self.terms:
                return util.getMissingET(METUtil.RefFinal, METUtil.ScaleSoftTermsDown)
            elif Systematics.MET_RESOSOFTTERMS_UP in self.terms:
                return util.getMissingET(METUtil.RefFinal, METUtil.ResoSoftTermsUp)
            elif Systematics.MET_RESOSOFTTERMS_DOWN in self.terms:
                return util.getMissingET(METUtil.RefFinal, METUtil.ResoSoftTermsDown)
            return util.getMissingET(METUtil.RefFinal)
        elif self.year == 2012:
            multisyst = METUtil.MultiSyst()
            if Systematics.MET_SCALESOFTTERMS_UP in self.terms:
                multisyst.setSyst(Systematics.MET_SCALESOFTTERMS_UP)
                return util.getMissingET(METUtil.RefFinal, multisyst)
            elif Systematics.MET_SCALESOFTTERMS_DOWN in self.terms:
                multisyst.setSyst(Systematics.MET_SCALESOFTTERMS_DOWN)
                return util.getMissingET(METUtil.RefFinal, multisyst)
            elif Systematics.MET_RESOSOFTTERMS_UP in self.terms:
                multisyst.setSyst(Systematics.MET_RESOSOFTTERMS_UP)
                return util.getMissingET(METUtil.RefFinal, multisyst)
            elif Systematics.MET_RESOSOFTTERMS_DOWN in self.terms:
                multisyst.setSyst(Systematics.MET_RESOSOFTTERMS_DOWN)
                return util.getMissingET(METUtil.RefFinal, multisyst)
            return util.getMissingET(METUtil.RefFinal)

    def passes(self, event):

        # reset the METUtility
        self.tool.reset()

        # These set up the systematic "SoftTerms_ptHard"
        self.tool.setNvtx(self.tree.nvtxsoftmet)

        if self.year == 2012:
            return self.passes_12(event)
        elif self.year == 2011:
            return self.passes_11(event)
        else:
            raise ValueError("No MET defined for year %d" % self.year)

    def passes_11(self, event):
        """
        JETS
        Always use setJetParameters since they may be recalibrated upstream
        https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/MissingETUtilityFAQ#If_I_recalibrate_correct_my_anal
        """
        self.tool.setJetParameters(
            event.jet_pt,
            self.tree.jet_eta_original,
            self.tree.jet_phi_original,
            event.jet_E,
            event.jet_AntiKt4LCTopo_MET_BDTMedium_wet,
            event.jet_AntiKt4LCTopo_MET_BDTMedium_wpx,
            event.jet_AntiKt4LCTopo_MET_BDTMedium_wpy,
            event.jet_AntiKt4LCTopo_MET_BDTMedium_statusWord)

        #self.tool.setOriJetParameters(self.tree.jet_pt_original)

        # Taus
        self.tool.setTauParameters(
            event.tau_pt,
            event.tau_eta,
            event.tau_phi,
            event.tau_MET_BDTMedium_wet,
            event.tau_MET_BDTMedium_wpx,
            event.tau_MET_BDTMedium_wpy,
            event.tau_MET_BDTMedium_statusWord)

        # Electrons
        self.tool.setMETTerm(
            METUtil.RefEle,
            event.MET_RefEle_BDTMedium_etx,
            event.MET_RefEle_BDTMedium_ety,
            event.MET_RefEle_BDTMedium_sumet)

        # Muons
        self.tool.setMETTerm(
            METUtil.MuonTotal,
            event.MET_Muon_Total_Staco_BDTMedium_etx,
            event.MET_Muon_Total_Staco_BDTMedium_ety,
            event.MET_Muon_Total_Staco_BDTMedium_sumet)

        # Note that RefMuon is not rebuilt from muons
        # -- it is a calorimeter term.
        self.tool.setMETTerm(
            METUtil.RefMuon,
            event.MET_RefMuon_Staco_BDTMedium_etx,
            event.MET_RefMuon_Staco_BDTMedium_ety,
            event.MET_RefMuon_Staco_BDTMedium_sumet)

        # Photons
        self.tool.setMETTerm(
            METUtil.RefGamma,
            event.MET_RefGamma_BDTMedium_etx,
            event.MET_RefGamma_BDTMedium_ety,
            event.MET_RefGamma_BDTMedium_sumet)

        """
        self.tool.setMETTerm(
            METUtil.SoftJets,
            event.MET_SoftJets_BDTMedium_etx,
            event.MET_SoftJets_BDTMedium_ety,
            event.MET_SoftJets_BDTMedium_sumet)
        """

        # Soft terms
        self.tool.setMETTerm(
            METUtil.SoftTerms,
            event.MET_CellOut_BDTMedium_etx,
            event.MET_CellOut_BDTMedium_ety,
            event.MET_CellOut_BDTMedium_sumet)

        MET = self.get_met()

        if self.verbose:
            log.info("Run: {0} Event: {1}".format(
                event.RunNumber,
                event.EventNumber))
            log.info("Recalculated MET: %.3f (original: %.3f)" % (
                     MET.et(), event.MET_RefFinal_BDTMedium_et))
            log.info("Recalculated MET phi: %.3f (original: %.3f)" % (
                     MET.phi(), event.MET_RefFinal_BDTMedium_phi))
            if (abs(MET.et() - event.MET_RefFinal_BDTMedium_et) /
                    event.MET_RefFinal_BDTMedium_et) > 0.1:
                log.warning("Large MET difference!")

        # update the MET with the shifted value
        self.tree.MET_etx_original = event.MET_RefFinal_BDTMedium_etx
        self.tree.MET_ety_original = event.MET_RefFinal_BDTMedium_ety
        self.tree.MET_et_original = event.MET_RefFinal_BDTMedium_et
        self.tree.MET_sumet_original = event.MET_RefFinal_BDTMedium_sumet
        self.tree.MET_phi_original = event.MET_RefFinal_BDTMedium_phi

        event.MET_RefFinal_BDTMedium_etx = MET.etx()
        event.MET_RefFinal_BDTMedium_ety = MET.ety()
        event.MET_RefFinal_BDTMedium_et = MET.et()
        event.MET_RefFinal_BDTMedium_sumet = MET.sumet()
        event.MET_RefFinal_BDTMedium_phi = MET.phi()

        return True

    def passes_12(self, event):
        # AntiTau MET calculation from Alex Tuna
        # If a selected tau matches a JVF jet, clear the corresponding jet weights
        # and set the tau weights to 1.0.
        # This must be applied after the tau selection but before the jet selection
        assert(len(event.taus) == 2)
        for tau in event.taus:
            # event.taus only contains selected taus at this point
            match = False
            for jet in event.jets:
                # event.jets contains all jets
                # Does this jet match the tau?
                if dR(tau.eta, tau.phi, jet.eta, jet.phi) < 0.4:
                    match = True
                    # Loop through subjets to find the JVF jets used for STVF
                    for k in xrange(jet.AntiKt4LCTopo_MET_wet.size()):
                        # If the subjet is a JVF jet, set weight to 0
                        if jet.AntiKt4LCTopo_MET_statusWord[k] == (0x3300 | 0x0001):
                            jet.AntiKt4LCTopo_MET_wet[k] = 0.0
                            jet.AntiKt4LCTopo_MET_wpx[k] = 0.0
                            jet.AntiKt4LCTopo_MET_wpy[k] = 0.0
            # If the tau has a matching jet, set the tau weights to 1
            if match:
                tau.MET_statusWord[0] = 1
                tau.MET_wet[0] = 1.0
                tau.MET_wpx[0] = 1.0
                tau.MET_wpy[0] = 1.0

        # this must be put before setting the jets parameters
        self.tool.setJetPUcode(MissingETTags.JPU_JET_JVFCUT)

        """
        JETS
        Always use setJetParameters since they may be recalibrated upstream
        https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/MissingETUtilityFAQ#If_I_recalibrate_correct_my_anal
        """
        self.tool.setJetParameters(
            event.jet_pt,
            self.tree.jet_eta_original,
            self.tree.jet_phi_original,
            event.jet_E,
            event.jet_AntiKt4LCTopo_MET_wet,
            event.jet_AntiKt4LCTopo_MET_wpx,
            event.jet_AntiKt4LCTopo_MET_wpy,
            event.jet_AntiKt4LCTopo_MET_statusWord)

        #self.tool.setOriJetParameters(event.jet_pt)

        # Taus
        self.tool.setTauParameters(
            event.tau_pt,
            event.tau_eta,
            event.tau_phi,
            event.tau_MET_wet,
            event.tau_MET_wpx,
            event.tau_MET_wpy,
            event.tau_MET_statusWord)

        # Electrons
        self.tool.setMETTerm(
            METUtil.RefEle,
            event.MET_RefEle_etx,
            event.MET_RefEle_ety,
            event.MET_RefEle_sumet)

        # Muons
        self.tool.setMETTerm(
            METUtil.MuonTotal,
            event.MET_Muon_Total_Staco_etx,
            event.MET_Muon_Total_Staco_ety,
            event.MET_Muon_Total_Staco_sumet)

        # Note that RefMuon is not rebuilt from muons
        # -- it is a calorimeter term.
        #self.tool.setMETTerm(
        #    METUtil.RefMuon,
        #    event.MET_RefMuon_Staco_etx,
        #    event.MET_RefMuon_Staco_ety,
        #    event.MET_RefMuon_Staco_sumet)

        # Photons
        self.tool.setMETTerm(
            METUtil.RefGamma,
            event.MET_RefGamma_etx,
            event.MET_RefGamma_ety,
            event.MET_RefGamma_sumet)

        # Soft terms
        self.tool.setMETTerm(
            METUtil.SoftTerms,
            event.MET_CellOut_Eflow_STVF_etx,
            event.MET_CellOut_Eflow_STVF_ety,
            event.MET_CellOut_Eflow_STVF_sumet)

        MET = self.get_met()

        if self.verbose:
            log.info("Run: {0} Event: {1}".format(
                event.RunNumber,
                event.EventNumber))
            log.info("Recalculated MET: %.3f (original: %.3f)" % (
                     MET.et(), event.MET_RefFinal_STVF_et))
            log.info("Recalculated MET phi: %.3f (original: %.3f)" % (
                     MET.phi(), event.MET_RefFinal_STVF_phi))
            if (abs(MET.et() - event.MET_RefFinal_STVF_et) /
                    event.MET_RefFinal_STVF_et) > 0.1:
                log.warning("Large MET difference!")

        # update the MET with the shifted value
        self.tree.MET_etx_original = event.MET_RefFinal_STVF_etx
        self.tree.MET_ety_original = event.MET_RefFinal_STVF_ety
        self.tree.MET_et_original = event.MET_RefFinal_STVF_et
        self.tree.MET_sumet_original = event.MET_RefFinal_STVF_sumet
        self.tree.MET_phi_original = event.MET_RefFinal_STVF_phi

        event.MET_RefFinal_STVF_etx = MET.etx()
        event.MET_RefFinal_STVF_ety = MET.ety()
        event.MET_RefFinal_STVF_et = MET.et()
        event.MET_RefFinal_STVF_sumet = MET.sumet()
        event.MET_RefFinal_STVF_phi = MET.phi()

        return True
